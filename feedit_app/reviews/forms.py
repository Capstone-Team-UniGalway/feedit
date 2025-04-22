from django import forms
from .models import Review, ReviewReply


class ReviewForm(forms.ModelForm):
    """Form for creating reviews."""
    
    class Meta:
        model = Review
        fields = ['rating', 'content', 'is_anonymous']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': '0',
                'max': '5',
                'step': '0.5'
            }),
            'content': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': '4',
                'placeholder': 'Write your review here...'
            }),
            'is_anonymous': forms.CheckboxInput(attrs={
                'class': 'checkbox'
            })
        }
        labels = {
            'is_anonymous': 'Post anonymously'
        }


class ReviewReplyForm(forms.ModelForm):
    """Form for replying to reviews."""
    
    class Meta:
        model = ReviewReply
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': '4',
                'placeholder': 'Write your reply here...'
            })
        }
