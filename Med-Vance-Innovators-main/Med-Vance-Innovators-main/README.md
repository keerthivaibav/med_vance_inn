MEDIxtract Server
MEDIxtract Server is a Flask-based web application designed to process image and PDF files, extract relevant data (like particulars and amounts), and store the results in an Excel file. It utilizes OpenAI's GPT model for text extraction and formatting, and supports image and PDF uploads.

Features
Upload image files (JPEG, PNG) or PDF files.
Extract text data from uploaded images using a remote API.
Extract text from PDFs and format it using OpenAI GPT.
Store the extracted and formatted data in an Excel file.
Download the generated Excel file.
Folder Structure
uploads/: Stores the uploaded image and PDF files.
excel_files/: Stores the generated Excel files containing the extracted data.
Tech Stack
Python: Backend development
Flask: Web framework
OpenAI GPT: For text extraction and formatting
PyPDF2: For extracting text from PDFs
openpyxl: For writing data to Excel files
requests: For making HTTP requests to external services
Installation
Clone the repository:


Set up a virtual environment:

bash
Copy code
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install the required dependencies:

bash
Copy code
pip install -r requirements.txt
Set your OpenAI API key in the openai.api_key variable:

python
Copy code
openai.api_key = 'your-openai-api-key'
Create the necessary folders:

bash
Copy code
mkdir uploads
mkdir excel_files
Usage
Start the Flask server:

bash
Copy code
python main.py <folder_path>
Replace <folder_path> with the path to the folder where your project files are located.

Access the app at http://127.0.0.1:5000/.

Uploading Files
Use the /post_image route to upload image or PDF files.
Processed data will be stored in an Excel file and can be downloaded from the /download_excel route.
Endpoints
GET /: Returns a welcome message.
POST /post_image: Uploads and processes an image or PDF file.
GET /download_excel: Downloads the generated Excel file.
Error Handling
The application will return appropriate error messages if file uploads fail or if issues occur during data extraction and processing.
Future Enhancements
Add support for additional file types.
Improve data extraction methods.
Add more customizable formatting options for extracted data.
Contributing
Feel free to fork this repository and submit pull requests for any improvements or bug fixes.

