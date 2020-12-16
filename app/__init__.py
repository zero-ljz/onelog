import os
import click
from flask import Flask
from .settings import config
from .extensions import db, toolbar, bootstrap
from .blueprints import main, auth
from .models import Option, User, Category, Tag, Post, Comment, Link

from sqlalchemy.sql.expression import func
from sqlalchemy import extract


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')

    # 初始化应用
    app = Flask(__name__)

    # 导入配置文件
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    toolbar.init_app(app)
    bootstrap.init_app(app)


    # 注册蓝图
    app.register_blueprint(main.main_bp)
    app.register_blueprint(auth.auth_bp)

    # 创建模板上下文
    @app.context_processor
    def make_template_context():
        options = {}
        for option in Option.query.all():
            options[option.name] = option.value

        categorys = Category.query.all()

        tags = Tag.query.order_by(Tag.name).all()

        comments = Comment.query.order_by(Comment.author).all()

        links = Link.query.order_by(Link.name).all()

        archives = db.session.query(extract('month', Post.created).label('month'), extract(
            'year', Post.created).label('year'), func.count('*').label('count')).group_by('month').all()

        return dict(options=options, categorys=categorys, tags=tags, archives=archives, comments=comments, links=links)

    # 创建Shell命令
    @ app.cli.command()
    @ click.option('--drop', is_flag=True, help='Create after drop.')
    def initdb(drop):
        """创建数据库
        """
        if drop:
            click.confirm(
                'This operation will delete the database, do you want to continue?', abort=True)
            db.drop_all()
            click.echo('Drop tables.')
        db.create_all()
        click.echo('Initialized database.')

    @ app.cli.command()
    def forge():
        """生成虚拟数据
        """
        from .fakes import fake_option, fake_user, fake_categorys, fake_tags, fake_posts, fake_comments, fake_links

        db.drop_all()
        db.create_all()

        click.echo('Generating blog information')
        fake_option()

        click.echo('Generating the administrator...')
        fake_user()

        click.echo('Generating categorys...')
        fake_categorys()

        click.echo('Generating tags...')
        fake_tags()

        click.echo('Generating posts...')
        fake_posts()

        click.echo('Generating comments...')
        fake_comments()

        click.echo('Generating links...')
        fake_links()

        click.echo('Done.')

    return app