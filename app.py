from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Airtable configuration
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.environ.get('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = os.environ.get('AIRTABLE_TABLE_NAME', 'Table 1')

def get_airtable_headers():
    return {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/next-company')
def get_next_company():
    try:
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
        params = {
            'filterByFormula': "OR({status} = 'Not Called', {status} = 'Call Back')",
            'maxRecords': 1,
            'sort[0][field]': 'business_name',
            'sort[0][direction]': 'asc'
        }
        
        response = requests.get(url, headers=get_airtable_headers(), params=params)
        data = response.json()
        
        if data.get('records'):
            record = data['records'][0]
            company = {
                'id': record['id'],
                'business_name': record['fields'].get('business_name', ''),
                'phone_number': record['fields'].get('phone_number', ''),
                'status': record['fields'].get('status', 'Not Called'),
                'tier': record['fields'].get('tier', 'Tier 3'),
                'website_status': record['fields'].get('website_status', 'None'),
                'seo_status': record['fields'].get('seo_status', 'None')
            }
            return jsonify(company)
        else:
            return jsonify({'error': 'No companies found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-company', methods=['POST'])
def update_company():
    try:
        data = request.json
        company_id = data.get('id')
        
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}/{company_id}"
        
        update_data = {
            'fields': {
                'status': data.get('status'),
                'notes': data.get('notes', ''),
                'last_updated': datetime.now().isoformat()
            }
        }
        
        if data.get('call_back_date'):
            update_data['fields']['call_back_date'] = data['call_back_date']
        
        if data.get('meeting_date'):
            update_data['fields']['meeting_date'] = data['meeting_date']
        
        response = requests.patch(url, headers=get_airtable_headers(), json=update_data)
        
        if response.status_code == 200:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to update'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

