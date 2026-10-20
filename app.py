from flask import Flask, render_template, request, jsonify
from database import create_tables
from services.gemini import get_response
from services.chat_service import (
    create_chat,
    get_all_chats,
    save_message,
    get_chat_history,
    rename_chat,
    delete_chat,
)

app = Flask(__name__)

create_tables()

@app.route("/")
def home():
    return render_template("chatbot.html")

@app.route("/new_chat", methods=["POST"])
def new_chat():
    try:
        title = request.json.get("title", "New Chat").strip()
        
        # ✅ Validate input
        if not title or len(title) > 100:
            return jsonify({"error": "Title must be 1-100 characters"}), 400
        
        chat_id = create_chat(title)
        return jsonify({"chat_id": chat_id})
    
    except Exception as e:
        print(f"❌ Error creating chat: {e}")
        return jsonify({"error": "Failed to create chat"}), 500

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        
        # ✅ Validate required fields
        if not data or "chat_id" not in data or "message" not in data:
            return jsonify({"error": "Missing chat_id or message"}), 400

        chat_id = data["chat_id"]
        user_message = data["message"].strip()
        mode = data.get("mode", "explain")

        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400

        history = get_chat_history(chat_id)

        save_message(chat_id, "user", user_message)
        reply = get_response(user_message, history, mode)
        save_message(chat_id, "assistant", reply)

        return jsonify({
            "reply": reply,
            "mode": mode
        })

    except Exception as e:
        print(f"❌ Chat error: {e}")
        return jsonify({
            "error": "Failed to get response",
            "details": str(e)
        }), 500

@app.route("/chats")
def chats():
    try:
        chats_list = get_all_chats()
        
        # ✅ CRITICAL FIX: Include message history
        for chat in chats_list:
            messages = get_chat_history(chat['id'])
            chat['messages'] = messages
        
        return jsonify(chats_list)
    except Exception as e:
        print(f"❌ Error fetching chats: {e}")
        return jsonify({"error": "Failed to fetch chats"}), 500

@app.route("/rename_chat", methods=["POST"])
def rename_chat_route():
    try:
        data = request.json
        
        if not data or "chat_id" not in data or "title" not in data:
            return jsonify({"error": "Missing chat_id or title"}), 400
        
        new_title = data["title"].strip()
        if not new_title or len(new_title) > 100:
            return jsonify({"error": "Title must be 1-100 characters"}), 400
        
        rename_chat(data["chat_id"], new_title)
        return jsonify({"success": True})
    
    except Exception as e:
        print(f"❌ Rename error: {e}")
        return jsonify({"error": "Failed to rename chat"}), 500

@app.route("/delete_chat", methods=["POST"])
def delete_chat_route():
    try:
        data = request.json
        
        if not data or "chat_id" not in data:
            return jsonify({"error": "Missing chat_id"}), 400
        
        delete_chat(data["chat_id"])
        return jsonify({"success": True})
    
    except Exception as e:
        print(f"❌ Delete error: {e}")
        return jsonify({"error": "Failed to delete chat"}), 500

if __name__ == "__main__":
    app.run(debug=False)  # ✅ Change to False for production