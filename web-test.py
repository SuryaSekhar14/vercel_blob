# pylint: skip-file

'''
This is a simple web application that allows you to manage your Vercel Blob storage.

It provides a simple interface to list, upload, and delete blobs, as well as to copy and download them.

Use this to test the code.
'''

import vercel_blob
import dotenv
import pprint
from flask import Flask, request, redirect
import os

# Set custom colors for progress bars using hex codes
vercel_blob.set_progress_bar_colours(
    desc="#FFFFFF",
    bar="#0055CC",
    text="#FF0000"
)

app = Flask(__name__)
dotenv.load_dotenv()
print("Using vercel_blob version:", vercel_blob.__version__)
print("Token present:", "yes" if os.environ.get('BLOB_READ_WRITE_TOKEN') else "no")
print("VERCEL_BLOB_DEBUG Debug mode:", os.environ.get('VERCEL_BLOB_DEBUG'))

# Function to generate the index HTML with blob list
def generate_index_html(blobs_data=None):
    blobs_html = ""
    cursor = ""
    
    if blobs_data and blobs_data.get("blobs"):
        for blob in blobs_data["blobs"]:
            url = blob.get("url", "")
            path = blob.get("pathname", url)
            size = blob.get("size", 0)
            size_str = f"{size} bytes" if size < 1024 else f"{size/1024:.2f} KB" if size < 1024*1024 else f"{size/(1024*1024):.2f} MB"
            
            # Use data-attribute to store URL for copying
            blobs_html += f"""
            <tr>
                <td><a href="{url}" target="_blank">{path}</a></td>
                <td>{size_str}</td>
                <td>
                    <form style="display:inline-block; margin-right: 5px;">
                        <input type="hidden" class="url-value" value="{url}">
                        <button type="button" class="button copy-button">Copy URL</button>
                    </form>
                    <a href="/metadata?url={url}" class="button show-button">Show</a>
                    <form action="/delete" method="post" style="display:inline-block;" onsubmit="return confirm('Are you sure you want to delete this blob?\\n{url}');">
                        <input type="hidden" name="url" value="{url}">
                        <button type="submit" class="button highlight-button">Delete</button>
                    </form>
                </td>
            </tr>
            """
        
        cursor = blobs_data.get("cursor", "")
    else:
        blobs_html = "<tr><td colspan='3'>No blobs found</td></tr>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Vercel Blob Operations</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
            h1, h2 {{ color: #9c27b0; }}
            h1 {{ text-align: center; padding: 8px 0; margin: 0; background-color: #f5f5f5; font-size: 18px; }}
            .container {{ display: flex; height: calc(100vh - 40px); }}
            .left-panel {{ flex: 1; overflow-y: auto; padding: 10px; border-right: 1px solid #eaeaea; }}
            .right-panel {{ flex: 1; overflow-y: auto; padding: 10px; }}
            .section {{ margin-bottom: 20px; padding: 15px; border: 1px solid #eaeaea; border-radius: 5px; }}
            button, input[type="submit"], .button {{ background-color: #9c27b0; color: white; border: none; padding: 8px 16px; 
                     border-radius: 4px; cursor: pointer; margin-right: 5px; text-decoration: none; display: inline-block; }}
            button:hover, input[type="submit"]:hover, .button:hover {{ background-color: #7b1fa2; }}
            input[type="text"], input[type="file"] {{ padding: 8px; margin-bottom: 10px; width: 100%; box-sizing: border-box; }}
            pre {{ background-color: #f1f1f1; padding: 10px; border-radius: 4px; overflow-x: auto; }}
            .highlight-button {{ background-color: #f44336; }}
            .highlight-button:hover {{ background-color: #d32f2f; }}
            .show-button {{ background-color: #4caf50; }}
            .show-button:hover {{ background-color: #388e3c; }}
            .copy-button {{ background-color: #2196f3; }}
            .copy-button:hover {{ background-color: #0b7dda; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f5f5f5; }}
            .blob-list {{ margin-top: 20px; }}
            .pagination {{ margin-top: 10px; }}
            .pagination a {{ display: inline-block; padding: 5px 10px; background-color: #9c27b0; color: white; 
                           text-decoration: none; border-radius: 4px; margin-right: 5px; }}
            .toast {{ 
                position: fixed; 
                bottom: 20px; 
                left: 50%; 
                transform: translateX(-50%); 
                background-color: #333; 
                color: white; 
                padding: 10px 20px; 
                border-radius: 4px; 
                opacity: 0; 
                transition: opacity 0.3s ease-in-out;
                z-index: 1000;
            }}
            .notifications {{ 
                position: fixed; 
                bottom: 20px; 
                right: 20px; 
                width: 300px; 
                z-index: 1000; 
            }}
            .notification {{ 
                background-color: #333; 
                color: white; 
                padding: 15px; 
                margin-bottom: 10px; 
                border-radius: 5px; 
                box-shadow: 0 2px 5px rgba(0,0,0,0.2); 
                animation: fadeIn 0.3s ease-in;
            }}
            .notification.success {{ background-color: #4caf50; }}
            .notification.error {{ background-color: #f44336; }}
            .notification.info {{ background-color: #2196f3; }}
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
        </style>
    </head>
    <body>
        <h1>Vercel Blob Operations</h1>
        
        <div class="container">
            <!-- Left Panel - Blob List -->
            <div class="left-panel">
                <h2>Blob List</h2>
                <div class="section">
                    <form action="/" method="get">
                        <label for="cursor">Cursor (optional):</label>
                        <input type="text" id="cursor" name="cursor" value="{cursor}">
                        <input type="submit" value="List Blobs">
                    </form>
                    
                    <div class="blob-list">
                        <table>
                            <tr>
                                <th>Path</th>
                                <th>Size</th>
                                <th>Actions</th>
                            </tr>
                            {blobs_html}
                        </table>
                        
                        <div class="pagination">
                            <a href="/">First Page</a>
                            {f'<a href="/?cursor={cursor}">Next Page</a>' if cursor else ''}
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Right Panel - Operations -->
            <div class="right-panel">
                <h2>Blob Operations</h2>
                
                <div class="section">
                    <h3>Upload a Blob</h3>
                    <form action="/upload" method="post" enctype="multipart/form-data">
                        <label for="file">Select a file:</label>
                        <input type="file" id="file" name="file" required>
                        <input type="checkbox" id="addRandomSuffix" name="addRandomSuffix">
                        <label for="addRandomSuffix">Add random suffix</label>
                        <input type="checkbox" id="allowOverwrite" name="allowOverwrite">
                        <label for="allowOverwrite">Allow overwrite</label>
                        <input type="submit" value="Upload">
                    </form>
                </div>
                
                <div class="section">
                    <h3>Get Blob Metadata</h3>
                    <form action="/metadata" method="get">
                        <label for="url">Blob URL:</label>
                        <input type="text" id="url" name="url" required>
                        <input type="submit" value="Get Metadata">
                    </form>
                </div>
                
                <div class="section">
                    <h3>Delete Blob</h3>
                    <form action="/delete" method="post">
                        <label for="delete_url">Blob URL:</label>
                        <input type="text" id="delete_url" name="url" required>
                        <input type="submit" value="Delete">
                    </form>
                </div>
                
                <div class="section">
                    <h3>Copy Blob</h3>
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
                    <h3>Download Blob</h3>
                    <form action="/download" method="get">
                        <label for="download_url">Blob URL:</label>
                        <input type="text" id="download_url" name="url" required>
                        <input type="submit" value="Download">
                    </form>
                </div>
            </div>
        </div>

        <div id="toast" class="toast"></div>
        <div id="notifications" class="notifications"></div>

        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            // Add click handlers to all copy buttons
            var copyButtons = document.querySelectorAll('.copy-button');
            copyButtons.forEach(function(button) {{
                button.addEventListener('click', function() {{
                    // Get the URL from the hidden input
                    var urlInput = this.parentNode.querySelector('.url-value');
                    var text = urlInput.value;
                    
                    // Copy to clipboard
                    try {{
                        navigator.clipboard.writeText(text).then(function() {{
                            // Success - show notification
                            showNotification('URL copied to clipboard', 'success');
                        }}).catch(function(err) {{
                            // Fallback for older browsers
                            fallbackCopyToClipboard(text);
                        }});
                    }} catch (err) {{
                        // Fallback for browsers that don't support clipboard API
                        fallbackCopyToClipboard(text);
                    }}
                }});
            }});
            
            function fallbackCopyToClipboard(text) {{
                // Create a temporary input element
                var input = document.createElement('input');
                input.style.position = 'fixed';
                input.style.opacity = 0;
                input.value = text;
                document.body.appendChild(input);
                
                // Select and copy the text
                input.select();
                document.execCommand('copy');
                
                // Remove the temporary element
                document.body.removeChild(input);
                
                // Show notification
                showNotification('URL copied to clipboard', 'success');
            }}
            
            // Check for messages in URL params
            checkForMessages();

            function checkForMessages() {{
                const urlParams = new URLSearchParams(window.location.search);
                const message = urlParams.get('message');
                const type = urlParams.get('type') || 'info';
                
                if (message) {{
                    showNotification(decodeURIComponent(message), type);
                    
                    // Clean up the URL by removing the message parameters
                    const cleanUrl = window.location.pathname;
                    window.history.replaceState({{}}, document.title, cleanUrl);
                }}
            }}
            
            function showToast(message) {{
                var toast = document.getElementById('toast');
                toast.textContent = message;
                toast.style.opacity = 1;
                
                // Hide toast after 2 seconds
                setTimeout(function() {{
                    toast.style.opacity = 0;
                }}, 2000);
            }}

            // New notification system that supports stacking
            window.showNotification = function(message, type) {{
                console.log('Notification: ' + type + ' - ' + message);
                
                var notifications = document.getElementById('notifications');
                var notification = document.createElement('div');
                notification.className = 'notification ' + type;
                notification.textContent = message;
                
                notifications.appendChild(notification);
                
                // Remove notification after 4 seconds
                setTimeout(function() {{
                    notification.style.opacity = '0';
                    setTimeout(function() {{
                        notifications.removeChild(notification);
                    }}, 300);
                }}, 4000);
            }};
        }});
        </script>
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

def list_all_blobs(cursor=None):
    blob_list = vercel_blob.list({
        'cursor': cursor if cursor else None,
    })
    return blob_list

def upload_a_blob(file_data, filename, add_random_suffix, allow_overwrite):
    resp = vercel_blob.put(filename, 
                           file_data, 
                           {
                               "addRandomSuffix": "true" if add_random_suffix else "false",
                               "allowOverwrite": "true"
                           },
                           verbose=True,
                           multipart=True
                        )
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
    }, verbose=True)
    return resp

def download_a_blob(url):
    resp = vercel_blob.download_file(url, verbose=True)
    return resp

@app.route('/')
def index():
    cursor = request.args.get('cursor')
    blobs_data = list_all_blobs(cursor)
    return generate_index_html(blobs_data)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "No file part", 400
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    
    add_random_suffix = 'addRandomSuffix' in request.form
    allow_overwrite = 'allowOverwrite' in request.form
    result = upload_a_blob(file.read(), file.filename, add_random_suffix, allow_overwrite)
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
        return redirect('/?message=No%20URL%20provided&type=error')
    
    try:
        result = delete_a_blob(url)
        print(f"Delete result: {result}")
        return redirect(f'/?message=Blob%20deleted%20successfully&type=success')
    except Exception as e:
        error_message = str(e).replace(' ', '%20')
        return redirect(f'/?message=Error:%20{error_message}&type=error')

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

if __name__ == '__main__':
    app.run(debug=True, port=8080) 