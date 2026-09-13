"""
DAKSH: J.A.R.V.I.S-Style Voice & Text Interface
Digital Assistant for Knowledge and Smart Handling

Features:
- Voice input/output (speech recognition & text-to-speech)
- Natural conversational interface
- Real-time visual feedback with animations
- Contextual awareness
- Multi-modal interaction (voice, text, visual)
"""

import uuid
import threading
import time
import re
from pathlib import Path
from typing import Any, Dict, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger

from config.settings import DAKSH_DATA_DIR
from daksh.cloud_storage import InteractionHistoryStore
from orchestrator.integration import OrchestratorSystem, SystemConfig
from llm_providers.router import LLMRouter, LLMRequest


class InteractionMode(Enum):
    """DAKSH interaction modes."""
    VOICE = "voice"              # Voice input/output
    TEXT = "text"                # Text input/output
    MULTIMODAL = "multimodal"    # Combined voice + text
    VISUAL = "visual"            # UI-based interaction


class DAKSHStatus(Enum):
    """DAKSH operational status."""
    IDLE = "idle"                # Waiting for input
    LISTENING = "listening"      # Recording voice
    THINKING = "thinking"        # Processing
    SPEAKING = "speaking"        # Playing response
    EXECUTING = "executing"      # Running task


@dataclass
class DAKSHConfig:
    """Configuration for DAKSH."""
    name: str = "DAKSH"
    voice_enabled: bool = True
    text_enabled: bool = True
    visual_effects: bool = True
    response_speed: float = 1.0   # 0.5x to 2.0x speed
    voice_profile: str = "neutral" # neutral, british, american, indian
    listen_timeout: float = 10.0  # Seconds
    context_memory: int = 10      # Remember last N interactions
    auto_execute: bool = False    # Auto-execute recognized commands
    personality: str = "professional"  # professional, friendly, casual
    data_directory: Optional[str] = None


@dataclass
class DAKSHInteraction:
    """Single interaction with DAKSH."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    mode: InteractionMode = InteractionMode.TEXT
    user_input: str = ""
    user_input_type: str = "text"  # text, voice, command
    system_response: str = ""
    response_type: str = "text"    # text, voice, visual
    status: DAKSHStatus = DAKSHStatus.IDLE
    execution_time_ms: float = 0.0
    confidence: float = 0.0        # Confidence in understanding
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class DAKSH:
    """
    Digital Assistant for Knowledge and Smart Handling
    
    J.A.R.V.I.S-Style Interface with:
    - Voice recognition and synthesis
    - Natural language understanding
    - Contextual awareness
    - Visual feedback and animations
    - Multi-provider LLM routing
    """
    
    def __init__(self, config: Optional[DAKSHConfig] = None):
        self.id = str(uuid.uuid4())
        self.config = config or DAKSHConfig()
        data_directory = Path(self.config.data_directory) if self.config.data_directory else DAKSH_DATA_DIR
        self.orchestrator = OrchestratorSystem(
            SystemConfig(knowledge_storage_path=str(data_directory / "knowledge_graph.json"))
        )
        self.llm_router = LLMRouter()
        
        self.status = DAKSHStatus.IDLE
        self.history_store = InteractionHistoryStore(data_directory)
        self.interaction_history = self._load_interaction_history()
        self.context_memory: Dict[str, Any] = {}
        self.current_interaction: Optional[DAKSHInteraction] = None
        
        # Voice components (lazy loaded)
        self.speech_recognizer = None
        self.text_to_speech = None
        self.recognizer_available = self._init_speech_recognition()
        self.tts_available = self._init_text_to_speech()
        
        logger.info(
            f"DAKSH initialized (ID: {self.id}) - "
            f"Voice: {'Enabled' if self.recognizer_available else 'Disabled'} | "
            f"TTS: {'Enabled' if self.tts_available else 'Disabled'}"
        )
    
    def _init_speech_recognition(self) -> bool:
        """Initialize speech recognition."""
        try:
            import speech_recognition
            self.speech_recognizer = speech_recognition.Recognizer()
            logger.info("Speech recognition initialized")
            return True
        except ImportError:
            logger.warning("speech_recognition not installed. Install with: pip install SpeechRecognition")
            return False
    
    def _init_text_to_speech(self) -> bool:
        """Initialize text-to-speech."""
        try:
            import pyttsx3
            self.text_to_speech = pyttsx3.init()
            
            # Set voice profile
            voices = self.text_to_speech.getProperty('voices')
            if len(voices) > 1:
                self.text_to_speech.setProperty('voice', voices[1].id)  # Use different voice
            
            # Set rate
            rate = max(50, min(300, int(150 * self.config.response_speed)))
            self.text_to_speech.setProperty('rate', rate)
            
            logger.info("Text-to-speech initialized")
            return True
        except ImportError:
            logger.warning("pyttsx3 not installed. Install with: pip install pyttsx3")
            return False
    
    def listen(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        Listen for voice input.
        """
        if not self.recognizer_available:
            logger.warning("Speech recognition not available")
            return None
        
        timeout = timeout or self.config.listen_timeout
        
        try:
            self._update_status(DAKSHStatus.LISTENING)
            self._play_sound("listening")  # Audio cue
            
            import speech_recognition
            with speech_recognition.Microphone() as source:
                audio = self.speech_recognizer.listen(source, timeout=timeout)
            
            try:
                text = self.speech_recognizer.recognize_google(audio)
                logger.info(f"[DAKSH] Heard: {text}")
                return text
            except speech_recognition.UnknownValueError:
                logger.warning("Could not understand audio")
                self.speak("I didn't quite catch that. Could you repeat?")
                return None
            except speech_recognition.RequestError as e:
                logger.error(f"Speech recognition error: {str(e)}")
                self.speak("Sorry, there was an issue with speech recognition.")
                return None
        
        except Exception as e:
            logger.error(f"Listen error: {str(e)}")
            return None
    
    def speak(self, text: str, wait: bool = True) -> None:
        """
        Speak text using text-to-speech.
        """
        if not self.tts_available:
            logger.debug(f"[DAKSH Speech] {text}")
            return
        
        try:
            self._update_status(DAKSHStatus.SPEAKING)
            self.text_to_speech.say(text)
            
            if wait:
                self.text_to_speech.runAndWait()
            
            self._update_status(DAKSHStatus.IDLE)
        
        except Exception as e:
            logger.error(f"Speak error: {str(e)}")
    
    def _play_sound(self, sound_type: str) -> None:
        """
        Play audio cues for interface feedback.
        """
        try:
            import winsound
            if sound_type == "listening":
                winsound.Beep(1000, 200)  # 1000Hz, 200ms
            elif sound_type == "thinking":
                winsound.Beep(800, 100)
            elif sound_type == "ready":
                winsound.Beep(1200, 300)
            elif sound_type == "error":
                winsound.Beep(400, 500)
        except ImportError:
            pass  # Not on Windows
    
    def process_input(self, user_input: str, input_type: str = "text") -> DAKSHInteraction:
        """
        Process user input (voice or text).
        """
        import time
        start_time = time.time()
        
        interaction = DAKSHInteraction(
            mode=InteractionMode.VOICE if input_type == "voice" else InteractionMode.TEXT,
            user_input=user_input,
            user_input_type=input_type,
            status=DAKSHStatus.THINKING
        )
        
        self._update_status(DAKSHStatus.THINKING)
        
        try:
            # Parse user input for commands
            command, params = self._parse_input(user_input)
            interaction.metadata["command"] = command
            interaction.metadata["params"] = params
            
            # Route to appropriate handler
            if command == "execute_objective":
                response = self._handle_execute_objective(params)
            elif command == "query_knowledge":
                response = self._handle_query_knowledge(params)
            elif command == "add_knowledge":
                response = self._handle_add_knowledge(params)
            elif command == "system_status":
                response = self._handle_system_status()
            elif command == "help":
                response = self._handle_help()
            else:
                response = self._handle_general_query(user_input)
            
            interaction.system_response = response
            interaction.status = DAKSHStatus.IDLE
            interaction.confidence = 0.85
            
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            interaction.system_response = f"I encountered an error: {str(e)}"
            interaction.status = DAKSHStatus.IDLE
            interaction.confidence = 0.0
        
        finally:
            interaction.execution_time_ms = (time.time() - start_time) * 1000
            interaction.completed_at = datetime.now()
            
            self.interaction_history.append(interaction)
            self._save_interaction_history()
            self.current_interaction = interaction
            self._update_context(interaction)
        
        return interaction

    def _load_interaction_history(self) -> List[DAKSHInteraction]:
        interactions = []
        for record in self.history_store.load():
            try:
                interactions.append(
                    DAKSHInteraction(
                        id=record["id"],
                        mode=InteractionMode(record["mode"]),
                        user_input=record["user_input"],
                        user_input_type=record["user_input_type"],
                        system_response=record["system_response"],
                        response_type=record["response_type"],
                        status=DAKSHStatus(record["status"]),
                        execution_time_ms=record["execution_time_ms"],
                        confidence=record["confidence"],
                        metadata=record["metadata"],
                        created_at=datetime.fromisoformat(record["created_at"]),
                        completed_at=(
                            datetime.fromisoformat(record["completed_at"])
                            if record["completed_at"]
                            else None
                        ),
                    )
                )
            except (KeyError, TypeError, ValueError) as error:
                logger.error(f"Skipping invalid DAKSH interaction history record: {error}")
        return interactions

    def _save_interaction_history(self) -> None:
        self.history_store.save(
            [
                {
                    "id": interaction.id,
                    "mode": interaction.mode.value,
                    "user_input": interaction.user_input,
                    "user_input_type": interaction.user_input_type,
                    "system_response": interaction.system_response,
                    "response_type": interaction.response_type,
                    "status": interaction.status.value,
                    "execution_time_ms": interaction.execution_time_ms,
                    "confidence": interaction.confidence,
                    "metadata": interaction.metadata,
                    "created_at": interaction.created_at.isoformat(),
                    "completed_at": (
                        interaction.completed_at.isoformat()
                        if interaction.completed_at
                        else None
                    ),
                }
                for interaction in self.interaction_history
            ]
        )
    
    def _parse_input(self, user_input: str) -> tuple[str, Dict[str, Any]]:
        """
        Parse user input to extract commands.
        """
        text = user_input.lower().strip()
        params = {}
        
        # Commands require an explicit leading action verb. Substring matching
        # would turn normal questions such as "What does DAKSH use?" into work.
        if match := re.match(r"^(?:execute|run|do)\s+(.+)$", text):
            command = "execute_objective"
            params["objective"] = match.group(1)
        elif match := re.match(r"^(?:query|search|find|ask)\s+(.+)$", text):
            command = "query_knowledge"
            params["query"] = match.group(1)
        elif re.match(r"^(?:remember|add|store|learn)\s+", text):
            command = "add_knowledge"
            params["content"] = user_input
        elif text in {"status", "how are you", "what's up"}:
            command = "system_status"
        elif text in {"help", "what can you do"}:
            command = "help"
        
        else:
            command = "general_query"
            params["query"] = user_input
        
        return command, params
    
    def _handle_execute_objective(self, params: Dict[str, Any]) -> str:
        """
        Handle objective execution command.
        """
        objective = params.get("objective", "")
        
        if not objective:
            return "I need to know what objective you'd like me to execute."
        
        self._update_status(DAKSHStatus.EXECUTING)
        self.speak(f"Executing objective: {objective}", wait=False)
        
        result = self.orchestrator.execute_objective(objective)
        
        self._update_status(DAKSHStatus.IDLE)
        
        return f"Objective completed. {result.get('synthesis', 'Task finished.')}"
    
    def _handle_query_knowledge(self, params: Dict[str, Any]) -> str:
        """
        Handle knowledge query command.
        """
        query = params.get("query", "")
        
        if not query:
            return "Please ask me something specific about your knowledge base."
        
        results = self.orchestrator.query_knowledge(query)
        
        if not results or not results.get("top_results"):
            return f"I couldn't find information about {query} in my knowledge base."
        
        top_result = results["top_results"][0]
        return f"Found: {top_result.get('label', 'Unknown')} with {top_result.get('score', 0):.1%} relevance."
    
    def _handle_add_knowledge(self, params: Dict[str, Any]) -> str:
        """
        Handle knowledge addition command.
        """
        content = params.get("content", "")
        
        if not content:
            return "Please provide content to add to my knowledge base."
        
        result = self.orchestrator.add_knowledge(
            title=f"Added at {datetime.now().isoformat()}",
            content=content,
            source="daksh_voice_input"
        )
        
        if result:
            return f"Added to knowledge base. Document ID: {result['document_id']}"
        else:
            return "Could not add to knowledge base."
    
    def _handle_system_status(self) -> str:
        """
        Handle system status query.
        """
        status = self.orchestrator.get_system_status()
        
        commander = status.get("commander", {})
        
        return (
            f"System operational. "
            f"{commander.get('active_objectives', 0)} objectives active, "
            f"{commander.get('workers_count', 0)} workers running. "
            f"All systems nominal."
        )
    
    def _handle_help(self) -> str:
        """
        Provide help information.
        """
        return (
            "I'm DAKSH, your Digital Assistant. You can ask me to: "
            "Execute objectives, query your knowledge base, add information, "
            "check system status, or ask general questions. "
            "Just speak naturally or type your request."
        )
    
    def _handle_general_query(self, user_input: str) -> str:
        """
        Handle general queries using LLM router.
        """
        memory_context, sources = self._retrieve_memory_context(user_input)
        # Create LLM request
        llm_request = LLMRequest(
            prompt=user_input,
            system_prompt=(
                "You are DAKSH, a helpful private local assistant. Respond concisely and naturally. "
                "Use the supplied private-memory excerpts only when they are relevant. "
                "Do not invent facts from memory.\n\n"
                f"Private-memory excerpts:\n{memory_context or 'No relevant saved memory.'}"
            ),
            task_type="general"
        )
        
        # Route decision
        decision = self.llm_router.decide(llm_request, use_skills=True)
        
        if not decision.use_llm:
            return "I can handle this with my local knowledge. Processing..."
        
        # Execute with routing
        response = self.llm_router.execute(llm_request, decision)
        
        if response.status == "success":
            citation_text = f"\n\nSources: {', '.join(sources)}" if sources else ""
            return f"{response.content}{citation_text}"
        else:
            return f"I encountered an issue: {response.error}"

    def _retrieve_memory_context(self, query: str) -> tuple[str, List[str]]:
        """Return small, source-traceable private-memory excerpts for a chat turn."""
        results = self.orchestrator.query_knowledge(query, top_k=3)
        if not results:
            return "", []
        excerpts: List[str] = []
        sources: List[str] = []
        for result in results.get("top_results", []):
            if result.get("type") != "chunk":
                continue
            data = result.get("data", {})
            excerpt = data.get("chunk_text")
            document_id = data.get("doc_id")
            if not isinstance(excerpt, str) or not isinstance(document_id, str):
                continue
            document = self.orchestrator.knowledge_graph.documents.get(document_id)
            if document is None or document.source == "system_execution":
                continue
            excerpts.append(f"[{document.title}] {excerpt}")
            if document.source and document.source not in sources:
                sources.append(document.source)
        return "\n".join(excerpts)[:2_000], sources[:3]
    
    def _update_status(self, new_status: DAKSHStatus) -> None:
        """
        Update DAKSH status.
        """
        self.status = new_status
        logger.debug(f"[DAKSH Status] {new_status.value}")
    
    def _update_context(self, interaction: DAKSHInteraction) -> None:
        """
        Update context memory with interaction.
        """
        self.context_memory[interaction.id] = {
            "input": interaction.user_input,
            "response": interaction.system_response,
            "time": interaction.created_at.isoformat(),
        }
        
        # Keep only recent interactions
        if len(self.context_memory) > self.config.context_memory:
            oldest_key = min(self.context_memory.keys())
            del self.context_memory[oldest_key]
    
    def interactive_session(self) -> None:
        """
        Start interactive DAKSH session.
        """
        print("\n" + "="*80)
        print("DAKSH - Digital Assistant for Knowledge and Smart Handling")
        print("="*80)
        print(f"Status: {self.status.value}")
        print("\nAvailable modes:")
        print("  [1] Voice input (speak your command)")
        print("  [2] Text input (type your command)")
        print("  [3] Hybrid (voice + text)")
        print("\nCommands: execute, query, add, status, help, quit")
        print("="*80 + "\n")
        
        self.speak("DAKSH online. Ready to assist.")
        
        while True:
            try:
                mode = input("\nDAKSH Mode [1/2/3/quit]: ").strip().lower()
                
                if mode == "quit" or mode == "q":
                    self.speak("Shutting down. Goodbye.")
                    break
                
                if mode == "1" and self.recognizer_available:
                    user_input = self.listen()
                    if user_input:
                        self.speak(f"Processing: {user_input}")
                        interaction = self.process_input(user_input, input_type="voice")
                
                elif mode == "2":
                    user_input = input("You: ").strip()
                    if user_input:
                        interaction = self.process_input(user_input, input_type="text")
                
                elif mode == "3":
                    if self.recognizer_available:
                        user_input = self.listen()
                    else:
                        user_input = input("You: ").strip()
                    
                    if user_input:
                        interaction = self.process_input(user_input, input_type="voice")
                
                else:
                    print("Invalid mode. Please try again.")
                    continue
                
                if 'interaction' in locals():
                    print(f"\nDAKSH: {interaction.system_response}")
                    
                    if self.config.voice_enabled and self.tts_available:
                        self.speak(interaction.system_response, wait=True)
                    
                    print(f"[Confidence: {interaction.confidence:.1%}, Time: {interaction.execution_time_ms:.0f}ms]")
            
            except KeyboardInterrupt:
                print("\n\nSession interrupted.")
                break
            except Exception as e:
                logger.error(f"Session error: {str(e)}")
                print(f"Error: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get DAKSH statistics.
        """
        return {
            "daksh_id": self.id,
            "status": self.status.value,
            "interactions": len(self.interaction_history),
            "voice_enabled": self.recognizer_available,
            "tts_enabled": self.tts_available,
            "context_size": len(self.context_memory),
            "last_interaction": (
                self.interaction_history[-1].created_at.isoformat()
                if self.interaction_history
                else "Never"
            )
        }
