from backend import app

if __name__ == '__main__':
    try:
        app.run(debug=True, threaded=True, host="0.0.0.0", port=80)
    except:
        app.run(debug=True, threaded=True, host="0.0.0.0", port=8080)
