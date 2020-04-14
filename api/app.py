from apps import create_app

application = app = create_app()

if __name__ == '__main__':
    #app.jinja_env.auto_reload = True
    #app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=False)
