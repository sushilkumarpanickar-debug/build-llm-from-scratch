"""
DAKSH Web Dashboard - J.A.R.V.I.S-Style Web Interface
"""

from pathlib import Path

from flask import Flask, jsonify, render_template, request

from daksh.interface import DAKSH, DAKSHConfig, InteractionMode
from scripts.setup import setup_llm_providers
from config.settings import DAKSH_WEB_HOST, DAKSH_WEB_PORT


def create_daksh_dashboard() -> Flask:
    """
    Create Flask app for DAKSH web dashboard.
    """
    project_root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(project_root / "templates"),
        static_folder=str(project_root / "static"),
    )
    
    # Initialize DAKSH
    daksh_config = DAKSHConfig(
        voice_enabled=True,
        text_enabled=True,
        visual_effects=True,
        personality="professional"
    )
    daksh = DAKSH(daksh_config)
    llm_router = setup_llm_providers()
    daksh.llm_router = llm_router
    
    # Dashboard routes
    @app.route('/')
    def index():
        """Main dashboard."""
        return render_template('daksh_dashboard.html')
    
    @app.route('/api/daksh/status')
    def get_status():
        """Get DAKSH status."""
        return jsonify(daksh.get_stats())
    
    @app.route('/api/daksh/interact', methods=['POST'])
    def interact():
        """Process user interaction."""
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "Expected a JSON object"}), 400

        user_input = data.get('input', '').strip()
        input_type = data.get('type', 'text')

        if not user_input:
            return jsonify({"error": "Empty input"}), 400
        if len(user_input) > 10_000:
            return jsonify({"error": "Input exceeds the 10,000 character limit"}), 400
        if input_type not in {"text", "voice"}:
            return jsonify({"error": "Unsupported input type"}), 400

        interaction = daksh.process_input(user_input, input_type)
        
        return jsonify({
            "id": interaction.id,
            "input": interaction.user_input,
            "response": interaction.system_response,
            "confidence": interaction.confidence,
            "time_ms": interaction.execution_time_ms,
            "status": interaction.status.value,
            "metadata": interaction.metadata
        })
    
    @app.route('/api/daksh/voice', methods=['POST'])
    def voice_input():
        """Handle voice input."""
        # This would receive audio data and process it
        data = request.json
        audio_data = data.get('audio')
        
        # Process audio (simplified)
        if daksh.recognizer_available:
            # In production, decode audio and use speech recognizer
            return jsonify({"status": "voice_processing"})
        else:
            return jsonify({"error": "Voice not available"}), 400
    
    @app.route('/api/daksh/speak', methods=['POST'])
    def speak():
        """Generate speech output."""
        data = request.json
        text = data.get('text', '')
        
        if daksh.tts_available:
            daksh.speak(text, wait=False)
            return jsonify({"status": "speaking"})
        else:
            return jsonify({"status": "tts_unavailable"})
    
    @app.route('/api/daksh/history')
    def get_history():
        """Get interaction history."""
        limit = min(max(request.args.get('limit', 50, type=int) or 50, 1), 100)
        
        history = [
            {
                "id": i.id,
                "input": i.user_input,
                "response": i.system_response,
                "time": i.created_at.isoformat(),
                "confidence": i.confidence
            }
            for i in daksh.interaction_history[-limit:]
        ]
        
        return jsonify({"history": history})
    
    @app.route('/api/router/stats')
    def router_stats():
        """Get LLM router statistics."""
        return jsonify(llm_router.get_stats())
    
    @app.route('/api/router/analyze', methods=['POST'])
    def analyze_routing():
        """Analyze routing decision for a query."""
        data = request.json
        query = data.get('query', '')
        task_type = data.get('task_type', 'general')
        
        from llm_providers.router import LLMRequest
        llm_request = LLMRequest(
            prompt=query,
            task_type=task_type
        )
        
        decision = llm_router.decide(llm_request, use_skills=True)
        
        return jsonify({
            "use_llm": decision.use_llm,
            "provider": decision.provider.value if decision.provider else None,
            "confidence": decision.confidence,
            "reason": decision.reason,
            "estimated_cost": decision.estimated_cost,
            "estimated_time_ms": decision.estimated_time_ms,
            "fallback_providers": [p.value for p in (decision.fallback_providers or [])]
        })
    
    return app


if __name__ == "__main__":
    app = create_daksh_dashboard()
    app.run(host=DAKSH_WEB_HOST, port=DAKSH_WEB_PORT, debug=False)
