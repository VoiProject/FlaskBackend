from backend import app

if __name__ == '__main__':
    # app.run(debug=True, port=80)
    try:
        app.run(debug=True, threaded=True, host="0.0.0.0", port=80)
    except:
        app.run(debug=True, threaded=True, host="0.0.0.0", port=8080)
