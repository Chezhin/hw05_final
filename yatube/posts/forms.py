from django import forms

from .models import Comment, Post


# тут разве не в правильном порядке импорты?
# я думал в django как раз стандартная библиотека
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Текст', 'group': 'Группа'}
        help_texts = {
            'text': 'Введите текст здесь',
            'group': 'Название группы',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
