from flask import Flask, request, jsonify
import os
import uuid
from supabase import create_client, Client
from werkzeug.utils import secure_filename

app = Flask(__name__)

# 1. Securely connect to your Supabase Project
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

@app.route('/api/posts', methods=['GET', 'POST'])
def handle_posts():
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            content = request.form.get('content')
            image_url = None
            
            # 2. Handle the Image Upload
            if 'image' in request.files:
                file = request.files['image']
                if file.filename != '':
                    # Create a safe, unique filename
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    
                    # Read the file and upload to Supabase Storage
                    file_bytes = file.read()
                    supabase.storage.from_("images").upload(
                        path=unique_filename, 
                        file=file_bytes, 
                        file_options={"content-type": file.content_type}
                    )
                    
                    # Get the public URL to save to the database
                    image_url = supabase.storage.from_("images").get_public_url(unique_filename)
            
            # 3. Save the Data to the Database
            supabase.table("posts").insert({
                "title": title, 
                "content": content, 
                "image_url": image_url
            }).execute()

            return jsonify({"status": "success"}), 201
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # 4. Handle fetching posts for the main page
    if request.method == 'GET':
        try:
            # Fetch all posts, newest first
            response = supabase.table("posts").select("*").order("created_at", desc=True).execute()
            return jsonify(response.data), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# Required for Vercel
def handler(event, context):
    return app(event, context)
