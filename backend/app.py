from flask import Flask, jsonify, abort

app = Flask(__name__)

users = [
    {
        'id': 1,
        "login": "Mykyta",
        "hash": "1234",
        "posts": ["1", "2"]
    },
    {
        'id': 2,
        "login": "Sergei",
        "hash": "1234",
        "posts": ["3"]
    },
]

posts = [
    {
        'id': 1,
        'title': 'post1 title',
        'short_description': 'post1 description',
        'long_description': 'post1 long description'
    },
    {
        'id': 2,
        'title': 'post2 title',
        'short_description': 'post2 description',
        'long_description': 'post2 long description'
    },
    {
        'id': 3,
        'title': 'post4 title',
        'short_description': 'post3 description',
        'long_description': 'post3 long description'
    },
    {
        'id': 4,
        'title': 'post4 title',
        'short_description': 'post4 description',
        'long_description': 'post4 long description'
    },
]


@app.route('/api/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = list(filter(lambda u: u['id'] == user_id, users))
    print('go here')
    if len(user) == 0:
        abort(404)
    return jsonify({'user': user[0]})


@app.route('/api/post/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = list(filter(lambda u: u['id'] == post_id, posts))
    if len(post) == 0:
        abort(404)
    return jsonify({'post': post[0]})


@app.route('/api/posts/user/<int:user_id>', methods=['GET'])
def get_user_posts(user_id):
    user = list(filter(lambda u: u['id'] == user_id, users))
    if len(user) == 0:
        abort(404)
    user = user[0]
    user_posts = user['posts']

    user_posts = list(filter(lambda u: u['id'] in user_posts, posts))
    if len(user_posts) == 0:
        abort(404)
    return jsonify({'user_posts': user_posts})


if __name__ == '__main__':
    app.run(debug=True)
