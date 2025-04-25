# pylint: skip-file

'''
This is a simple web application that allows you to manage your Vercel Blob storage.

It provides a simple interface to list, upload, and delete blobs, as well as to copy and download them.

Use this to test the code.
'''

import vercel_blob
import dotenv
import pprint
from flask import Flask, request

# Set custom colors for progress bars using hex codes
vercel_blob.set_progress_bar_colours(
    desc="#FFFFFF",
    bar="#000000",
    text="#FF0000"
)

app = Flask(__name__)
dotenv.load_dotenv()
print("Using vercel_blob version:", vercel_blob.__version__)

# HTML template for the main page
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Vercel Blob Operations</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #9c27b0; }
        .section { margin-bottom: 30px; padding: 15px; border: 1px solid #eaeaea; border-radius: 5px; }
        button, input[type="submit"] { background-color: #9c27b0; color: white; border: none; padding: 8px 16px; 
                 border-radius: 4px; cursor: pointer; }
        button:hover, input[type="submit"]:hover { background-color: #7b1fa2; }
        input[type="text"], input[type="file"] { padding: 8px; margin-bottom: 10px; width: 100%; box-sizing: border-box; }
        pre { background-color: #f1f1f1; padding: 10px; border-radius: 4px; overflow-x: auto; }
        .highlight-button { background-color: #f44336; }
        .highlight-button:hover { background-color: #d32f2f; }
        a.button { text-decoration: none; display: inline-block; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>Vercel Blob Operations</h1>
    
    <div class="section">
        <h2>List All Blobs</h2>
        <form action="/list" method="get">
            <label for="cursor">Cursor (optional):</label>
            <input type="text" id="cursor" name="cursor">
            <input type="submit" value="List Blobs">
        </form>
        <a href="/manage" class="button" style="background-color: #9c27b0; color: white; padding: 8px 16px; border-radius: 4px; margin-top: 10px; display: inline-block;">Manage Blobs (with Delete)</a>
    </div>
    
    <div class="section">
        <h2>Upload a Blob</h2>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <label for="file">Select a file:</label>
            <input type="file" id="file" name="file" required>
            <input type="checkbox" id="addRandomSuffix" name="addRandomSuffix">
            <label for="addRandomSuffix">Add random suffix</label>
            <input type="submit" value="Upload">
        </form>
    </div>
    
    <div class="section">
        <h2>Get Blob Metadata</h2>
        <form action="/metadata" method="get">
            <label for="url">Blob URL:</label>
            <input type="text" id="url" name="url" required>
            <input type="submit" value="Get Metadata">
        </form>
    </div>
    
    <div class="section">
        <h2>Delete Blob</h2>
        <form action="/delete" method="post">
            <label for="delete_url">Blob URL:</label>
            <input type="text" id="delete_url" name="url" required>
            <input type="submit" value="Delete">
        </form>
    </div>
    
    <div class="section">
        <h2>Copy Blob</h2>
        <form action="/copy" method="post">
            <label for="copy_url">Source Blob URL:</label>
            <input type="text" id="copy_url" name="url" required>
            <label for="target_path">Target Path:</label>
            <input type="text" id="target_path" name="target_path" required>
            <input type="checkbox" id="copy_addRandomSuffix" name="addRandomSuffix">
            <label for="copy_addRandomSuffix">Add random suffix</label>
            <input type="submit" value="Copy">
        </form>
    </div>
    
    <div class="section">
        <h2>Download Blob</h2>
        <form action="/download" method="get">
            <label for="download_url">Blob URL:</label>
            <input type="text" id="download_url" name="url" required>
            <input type="submit" value="Download">
        </form>
    </div>
</body>
</html>
"""

# Function to generate result HTML
def result_template(title, data):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #9c27b0; }}
            pre {{ background-color: #f1f1f1; padding: 10px; border-radius: 4px; overflow-x: auto; }}
            a {{ display: inline-block; margin-top: 20px; background-color: #9c27b0; color: white; 
                text-decoration: none; padding: 8px 16px; border-radius: 4px; }}
            a:hover {{ background-color: #7b1fa2; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <pre>{pprint.pformat(data)}</pre>
        <a href="/">Back to Home</a>
    </body>
    </html>
    """

# HTML template for blob management page with one-click deletion
def manage_blobs_template(blobs_data):
    blobs_html = ""
    if blobs_data.get("blobs"):
        for blob in blobs_data["blobs"]:
            url = blob.get("url", "")
            path = blob.get("pathname", url)
            size = blob.get("size", 0)
            size_str = f"{size} bytes" if size < 1024 else f"{size/1024:.2f} KB" if size < 1024*1024 else f"{size/(1024*1024):.2f} MB"
            
            blobs_html += f"""
            <tr>
                <td><a href="{url}" target="_blank">{path}</a></td>
                <td>{size_str}</td>
                <td>
                    <form action="/delete_confirm" method="post" style="display: inline;">
                        <input type="hidden" name="url" value="{url}">
                        <button type="submit" class="highlight-button">Delete</button>
                    </form>
                </td>
            </tr>
            """
    
    next_cursor = blobs_data.get("cursor", "")
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Manage Blobs</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #9c27b0; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f5f5f5; }}
            a {{ color: #9c27b0; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            .pagination {{ margin-top: 20px; }}
            .pagination a {{ display: inline-block; padding: 8px 16px; background-color: #9c27b0; color: white; 
                          text-decoration: none; border-radius: 4px; margin-right: 5px; }}
            .pagination a:hover {{ background-color: #7b1fa2; }}
        </style>
    </head>
    <body>
        <h1>Manage Blobs</h1>
        <table>
            <tr>
                <th>Path</th>
                <th>Size</th>
                <th>Actions</th>
            </tr>
            {blobs_html}
        </table>
        <div class="pagination">
            <a href="/manage">First Page</a>
            {f'<a href="/manage?cursor={next_cursor}">Next Page</a>' if next_cursor else ''}
        </div>
        <a href="/" style="display: inline-block; margin-top: 20px; background-color: #9c27b0; color: white; 
           text-decoration: none; padding: 8px 16px; border-radius: 4px;">Back to Home</a>
    </body>
    </html>
    """

def delete_confirmation_template(url):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Confirm Delete</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #9c27b0; }}
            .warning {{ color: #f44336; font-weight: bold; }}
            .actions {{ margin-top: 30px; }}
            button {{ padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; }}
            .delete-btn {{ background-color: #f44336; color: white; }}
            .delete-btn:hover {{ background-color: #d32f2f; }}
            .cancel-btn {{ background-color: #777; color: white; }}
            .cancel-btn:hover {{ background-color: #555; }}
            pre {{ background-color: #f1f1f1; padding: 10px; border-radius: 4px; overflow-x: auto; }}
        </style>
    </head>
    <body>
        <h1>Confirm Delete</h1>
        <p class="warning">Are you sure you want to delete this blob?</p>
        <pre>{url}</pre>
        
        <div class="actions">
            <form action="/delete" method="post" style="display: inline;">
                <input type="hidden" name="url" value="{url}">
                <button type="submit" class="delete-btn">Yes, Delete</button>
            </form>
            <a href="/manage"><button type="button" class="cancel-btn">Cancel</button></a>
        </div>
    </body>
    </html>
    """

def list_all_blobs(cursor=None):
    blob_list = vercel_blob.list({
        'cursor': cursor if cursor else None,
    })
    return blob_list

def upload_a_blob(file_data, filename, add_random_suffix):
    resp = vercel_blob.put(filename, file_data, {
        "addRandomSuffix": "true" if add_random_suffix else "false",
    }, verbose=True)
    return resp

def get_blob_metadata(url):
    resp = vercel_blob.head(url)
    return resp

def delete_a_blob(url):
    resp = vercel_blob.delete([url])
    return resp

def copy_a_blob(url, target_path, add_random_suffix):
    resp = vercel_blob.copy(url, target_path, {
        "addRandomSuffix": "true" if add_random_suffix else "false"
    })
    return resp

def download_a_blob(url):
    resp = vercel_blob.download_file(url, verbose=True)
    return resp

@app.route('/')
def index():
    return INDEX_HTML

@app.route('/list')
def list_blobs():
    cursor = request.args.get('cursor')
    result = list_all_blobs(cursor)
    return result_template("Blob List Results", result)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "No file part", 400
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    
    add_random_suffix = 'addRandomSuffix' in request.form
    result = upload_a_blob(file.read(), file.filename, add_random_suffix)
    return result_template("Upload Results", result)

@app.route('/metadata')
def metadata():
    url = request.args.get('url')
    if not url:
        return "No URL provided", 400
    
    try:
        result = get_blob_metadata(url)
        return result_template("Blob Metadata", result)
    except Exception as e:
        return result_template("Error", str(e))

@app.route('/delete', methods=['POST'])
def delete():
    url = request.form.get('url')
    if not url:
        return "No URL provided", 400
    
    try:
        result = delete_a_blob(url)
        return result_template("Delete Results", result)
    except Exception as e:
        return result_template("Error", str(e))

@app.route('/copy', methods=['POST'])
def copy():
    url = request.form.get('url')
    target_path = request.form.get('target_path')
    add_random_suffix = 'addRandomSuffix' in request.form
    
    if not url or not target_path:
        return "Missing URL or target path", 400
    
    try:
        result = copy_a_blob(url, target_path, add_random_suffix)
        return result_template("Copy Results", result)
    except Exception as e:
        return result_template("Error", str(e))

@app.route('/download')
def download():
    url = request.args.get('url')
    if not url:
        return "No URL provided", 400
    
    try:
        result = download_a_blob(url)
        return result_template("Download Results", result)
    except Exception as e:
        return result_template("Error", str(e))

@app.route('/manage')
def manage():
    cursor = request.args.get('cursor')
    result = list_all_blobs(cursor)
    return manage_blobs_template(result)

@app.route('/delete_confirm', methods=['POST'])
def delete_confirm():
    url = request.form.get('url')
    if not url:
        return "No URL provided", 400
    
    return delete_confirmation_template(url)

if __name__ == '__main__':
    app.run(debug=True, port=8080) 