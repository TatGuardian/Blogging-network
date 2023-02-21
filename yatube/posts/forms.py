from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Text of the post here',
            'group': 'Name of the group',
        }
        help_texts = {
            'text': 'Text of the post here',
            'group': 'Name of group if any'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Text of the comment'
        }
        help_texts = {
            'text': 'Text of the comment'
        }
