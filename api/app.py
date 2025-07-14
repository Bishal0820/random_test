from flask import Flask, render_template, request, jsonify
import boto3
import os

app = Flask(__name__)

# TODO: Set your AWS credentials (or use environment variables/instance roles)
SSM_PARAMETER_NAME = os.environ.get('SSM_PARAMETER_NAME')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL')

ssm = boto3.client('ssm', region_name='us-east-1')  # Change region if needed
sns = boto3.client('sns', region_name='us-east-1')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    input_password = data.get('password')
    if not input_password:
        return jsonify({'success': False, 'message': 'Missing password'}), 400
    try:
        response = ssm.get_parameter(Name=SSM_PARAMETER_NAME, WithDecryption=True)
        stored_password = response['Parameter']['Value']
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching password: {str(e)}'}), 500
    if input_password != stored_password:
        return jsonify({'success': False, 'message': 'Incorrect password'}), 401
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message='Your password was accepted! This is a confirmation email.',
            Subject='Password Accepted - Confirmation',
            MessageAttributes={
                'email': {
                    'DataType': 'String',
                    'StringValue': RECIPIENT_EMAIL
                }
            }
        )
        return jsonify({'success': True, 'message': 'Email sent successfully!'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error sending email: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)