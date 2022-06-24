"""Database models."""
from tortoise import fields
from tortoise.models import Model


class Source(Model):
    slug_name = fields.CharField(max_length=126, pk=True)

    def __str__(self) -> str:
        return self.slug_name


class Tag(Model):
    tag_id = fields.IntField(pk=True)
    title = fields.CharField(max_length=126)  # TODO

    def __str__(self) -> str:
        return f'#{self.tag_id} {self.title}'


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
        fields.ManyToManyField('models.Tag', related_name='articles')
    )

    target_upload_name = fields.CharField(max_length=255, null=True)

    def __str__(self) -> str:
        return f'{self.source.slug_name}:{self.slug_name}'

    class Meta:
        unique_together = ('source', 'slug_name')
