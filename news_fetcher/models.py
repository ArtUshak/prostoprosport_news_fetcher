"""Database models."""
from tortoise import fields
from tortoise.models import Model


class Source(Model):
    slug_name = fields.CharField(max_length=126, pk=True)

    def __str__(self) -> str:
        return self.slug_name


class Tag(Model):
    tag_id = fields.IntField(pk=True)
    title = fields.CharField(max_length=126, unique=True)  # TODO

    def __str__(self) -> str:
        return f'#{self.tag_id} {self.title}'


class ArticleTag(Model):
    tag: 'fields.relational.ForeignKeyRelation[Tag]' = (
        fields.ForeignKeyField('models.Tag')
    )
    article: 'fields.relational.ForeignKeyRelation[Article]' = (
        fields.ForeignKeyField('models.Article')
    )

    class Meta:
        unique_together = ('tag', 'article')
        table = 'article_m2m_tag'


class Article(Model):
    article_id = fields.IntField(pk=True)

    source: 'fields.relational.ForeignKeyRelation[Source]' = (
        fields.ForeignKeyField('models.Source', related_name='articles')
    )
    slug_name = fields.CharField(max_length=1023)  # TODO

    title = fields.TextField()
    date = fields.DatetimeField(null=True)
    source_url = fields.TextField()
    source_url_ok = fields.BooleanField(null=True)

    author_name = fields.TextField(null=True)
    wikitext_paragraphs = fields.JSONField(null=True)
    misc_data = fields.JSONField()
    tags: 'fields.relational.ManyToManyRelation[Tag]' = (
        fields.ManyToManyField(
            'models.Tag', related_name='articles', through='article_m2m_tag'
        )
    )

    uploaded = fields.BooleanField(default=False)

    def __str__(self) -> str:
        return f'{self.source.slug_name}:{self.slug_name}'

    class Meta:
        unique_together = ('source', 'slug_name')
