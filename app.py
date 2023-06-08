from flask import Flask, render_template, request
from extractemail import get_vendor_emails

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/psd', methods=['GET', 'POST'])
def psd():
    if request.method == 'POST':
        product_name = request.form['product_name']
        emails_list = get_vendor_emails(product_name)
        return render_template('result.html', emails_list=emails_list)
    return render_template('index.html')

@app.route('/pbm')
def pbm():
    return 'Coming Soon'

if __name__ == '__main__':
    app.run(debug=True)
