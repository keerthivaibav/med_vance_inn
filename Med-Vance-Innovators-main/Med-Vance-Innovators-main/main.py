import os
import sys
from flask import Flask, Blueprint, request, jsonify, send_file
import requests
import re
import logging
import openai
import openpyxl
from werkzeug.utils import secure_filename
import json
import PyPDF2

UPLOAD_FOLDER = 'uploads'
EXCEL_FOLDER = 'excel_files'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Set your OpenAI API key
openai.api_key = 'OPENAI_API_KEY'

# Ensure the upload and Excel folders exist
for folder in [UPLOAD_FOLDER, EXCEL_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def process_folder(folder_path):
    
    # Define the blueprint
    main = Blueprint('main', __name__)

    @main.route('/')
    def index():
        return "Welcome to MEDIExtract Server!"

    @main.route('/post_image', methods=['POST'])
    def post_image():
        if 'encoded_image' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['encoded_image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            # Process based on file extension (PDF or image)
            if filename.lower().endswith('.pdf'):
                extracted_data = process_pdf(file_path)
            else:
                extracted_data = process_image(file_path)

            if extracted_data and 'extractedData' in extracted_data:
                formatted_data = format_data_with_openai(extracted_data['extractedData'])

                if formatted_data:
                    try:
                        formatted_data = formatted_data.replace('\n\n', '\n').strip()
                        output_path = os.path.join(EXCEL_FOLDER, 'extracted_data7.xlsx')
                        create_excel_file(output_path, formatted_data)
                        return jsonify({'message': 'Excel file created', 'file_path': output_path}), 200

                    except Exception as e:
                        logging.error(f"Error creating Excel file: {e}")
                        return jsonify({'error': 'Error creating Excel file'}), 500

                else:
                    return jsonify({'error': 'No formatted data found'}), 400

            else:
                logging.error(f"Error in extracted data: {extracted_data}")
                return jsonify(extracted_data), 400

        return jsonify({'error': 'No file provided or invalid file type'}), 400

    @main.route('/download_excel', methods=['GET'])
    def download_excel():
        file_name = 'extracted_data.xlsx'
        file_path = os.path.join(EXCEL_FOLDER, file_name)

        if os.path.exists(file_path):
            return send_file(file_path, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             download_name=file_name, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def process_image(image_path):
        endpoint_url = 'https://lens.google.com/v3/upload'

        try:
            image_bytes = read_image_file(image_path)
            files = {
                'encoded_image': (os.path.basename(image_path), image_bytes, f'image/{image_path.rsplit(".", 1)[1].lower()}')
            }

            logging.info('Sending request to endpoint...')
            response = requests.post(endpoint_url, files=files, timeout=120)
            response.raise_for_status()

            regex_pattern = r'",\[\[(\["(?:.*?)(?:",".*?)*"\])\],'  # Adjust regex pattern as needed
            match = re.search(regex_pattern, response.text)

            extracted_data = {}

            if match:
                extracted_data = {
                    'extractedData': match.group(1),
                }
            else:
                extracted_data = {
                    'message': 'No data matched the regex pattern.',
                    'raw_response': response.text
                }

            return extracted_data

        except requests.RequestException as e:
            logging.error('Request failed', exc_info=True)
            return {'error': 'Error posting image to external server'}

        except Exception as e:
            logging.error('Error processing image', exc_info=True)
            return {'error': 'Error processing image'}

    def process_pdf(file_path):
        try:
            extracted_text = extract_pdf_text(file_path)
            prompt = f"Extract particulars and amounts from this PDF content:\n{extracted_text}"

            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an assistant who extracts particulars and amounts from PDFs."},
                    {"role": "user", "content": prompt}
                ]
            )

            extracted_data = response['choices'][0]['message']['content']
            return {'extractedData': extracted_data}

        except Exception as e:
            logging.error('Error processing PDF file', exc_info=True)
            return {'error': 'Error processing PDF file'}

    def extract_pdf_text(pdf_path):
        text = ""
        try:
            with open(pdf_path, "rb") as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                for page in reader.pages:
                    text += page.extract_text()
        except Exception as e:
            logging.error(f"Error reading PDF: {e}")
        return text

    def read_image_file(file_path):
        with open(file_path, 'rb') as image_file:
            return image_file.read()

    def format_data_with_openai(extracted_data_string):
        prompt = (
            "Format the following extracted data into CSV format. "
            "Ensure the output is a plain text CSV where each row represents a data entry and columns are separated by commas. "
            "The first row should be the header. Maintain the original data structure and do not add or modify fields. Provide the string data within quotes. "
            "If any data is missing, leave the corresponding fields empty. Extract products and amount columns only. Clean and organize the data as necessary:\n\n"
            f"{extracted_data_string}"
        )
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "You are a helpful assistant that formats data into a structured CSV."},
                          {"role": "user", "content": prompt}],
                max_tokens=1500
            )

            formatted_data_string = response.choices[0].message['content'].strip()
            logging.debug(f"OpenAI response: {formatted_data_string}")

            return formatted_data_string

        except Exception as e:
            logging.error(f"Error formatting data with OpenAI: {e}")
            return None

    def create_excel_file(output_path, formatted_data):
        try:
            workbook = openpyxl.Workbook()
            sheet = workbook.active

            lines = formatted_data.strip().split('\n')

            for row_index, line in enumerate(lines):
                cells = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', line)
                cells = [cell.strip('"') for cell in cells]

                for col_index, cell in enumerate(cells):
                    if cell:
                        sheet.cell(row=row_index + 1, column=col_index + 1, value=cell)

            workbook.save(output_path)

        except Exception as e:
            logging.error(f"Error creating Excel file: {e}")
            raise

    # Create the Flask app and register the blueprint
    app = Flask(__name__)
    app.register_blueprint(main)

    app.run(debug=True)

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <folder_path>")
        sys.exit(1)

    folder_path = sys.argv[1]
    process_folder(folder_path)

if __name__ == "__main__":
    main()
