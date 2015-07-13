import sys

from django.conf import settings

from wsgiref import simple_server
simple_server.ServerHandler.http_version = "1.1"
#Chrome may not send If-None-Match is when the response includes an "HTTP/1.0" instead of an "HTTP/1.1" status line. Some servers, such as Django's development server, send an older header (probably because they do not support keep-alive) and when they do so, ETags don't work in Chrome.

settings.configure(
	DEBUG=True,
	SECRET_KEY='thisisthesecretkey',
	ROOT_URLCONF=__name__,
	MIDDLEWARE_CLASSES=(
		'django.middleware.common.CommonMiddleware',
		'django.middleware.csrf.CsrfViewMiddleware',
		'django.middleware.clickjacking.XFrameOptionsMiddleware',
	),
)


from django import forms
from django.conf.urls import url
from django.http import HttpResponse,HttpResponseBadRequest
from django.core.cache import cache
from django.views.decorators.http import etag

from io import BytesIO
from PIL import Image, ImageDraw
import hashlib
	
class ImageForm(forms.Form):
	height = forms.IntegerField(min_value=1, max_value=2000)
	width = forms.IntegerField(min_value=1, max_value=2000)
	
	def generate(self, image_format='PNG'):
		height=self.cleaned_data['height']
		width=self.cleaned_data['width']
		key='{}.{}.{}'.format(width,height,image_format)
		content=cache.get(key)
		if content is None:
			print 'not found in cache'
			image=Image.new('RGB', (width,height))
			draw=ImageDraw.Draw(image)
			text='{} X {}'.format(width,height)
			textwidth, textheight = draw.textsize(text)
			if textwidth < width and textheight < height:
				texttop = (height-textheight) // 2
				textleft = (width-textwidth) // 2
				draw.text((textleft,texttop), text, fill=(255,255,255))
			content=BytesIO()
			image.save(content, image_format)
			content.seek(0)
			cache.set(key, content, 60*60)
		return content

def generate_etag(request, width, height):
	content='Placeholder: %s x %s' % (width, height)
	return hashlib.sha1(content.encode('utf-8')).hexdigest()
		
def index(request):
	return HttpResponse('Hello World')

@etag(generate_etag)
def placeholder(request, width, height):
	print '%s x %s' % (width,height)
	form = ImageForm({'height':height, 'width':width})
	if form.is_valid():
		#height=form.cleaned_data['height']
		#width=form.cleaned_data['width']
		image=form.generate()
		return HttpResponse(image, content_type='image/png')
	else:
		return HttpResponseBadRequest('Invalid Image Request')
		

urlpatterns = (
	url(r'^$', index, name='homepage'),
	url(r'^image/(?P<width>[0-9]+)x(?P<height>[0-9]+)/$', placeholder, name='placeholder'),
)


if __name__ == "__main__":
	from django.core.management import execute_from_command_line
	execute_from_command_line(sys.argv)

