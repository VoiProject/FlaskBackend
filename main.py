from backend import app

if __name__ == '__main__':
    app.run(debug=True, port=80)
    # app.run(debug=True, threaded=True, host="0.0.0.0", port=80)

