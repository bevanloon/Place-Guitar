import os
import random
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.api import images

class IncomingRequests(db.Model):
    headers = db.TextProperty()
    remote_addr = db.StringProperty()
    date = db.DateTimeProperty(auto_now=True)

class Guitars(db.Model):
    name = db.StringProperty()
    rand = db.FloatProperty()
    image = db.BlobProperty()

class GetGuitarImage(webapp.RequestHandler):
  def get(self, awidth=None, aheight=None):
    #log the request - super basic logging - just throw the headers into a text and grab the remote address
    ir = IncomingRequests()
    ir.headers = str(self.request.headers)
    ir.remote_addr = self.request.remote_addr
    ir.put()
    
    #get a random guitar using our "rand" in the model
    rand_number = random.random()
    guitar_to_display = Guitars.all().order('rand').filter('rand >=', rand_number).get()
    if guitar_to_display is None:
      guitar_to_display = Guitars.all().order('rand').get()
    
    an_image = images.Image(guitar_to_display.image)
    
    #get our width and height - set defaults from the actual image
    # if for some reason the arguments passed in are not integers
    try:
      required_width = int(awidth)
    except:
      required_width = an_image.width
    try:
      required_height = int(aheight)
    except:
      required_height = an_image.height

    #hard limit at 2000px - design decision
    if required_width > 2000:
      required_width = 2000
    if required_height > 2000:
      required_height = 2000
    
    #work out our aspect ratios
    current_aspect_ratio = float(an_image.width) / float(an_image.height)
    required_aspect_ratio = float(required_width) / float(required_height)
    
    if current_aspect_ratio > required_aspect_ratio:
      #resize height, crop width
      an_image.resize(height = required_height)
      an_image.execute_transforms()
      trim_ratio = float(required_width) / float(an_image.width)
      x_left = (1.0 - trim_ratio) / 2.0
      an_image.crop(x_left, 0.0, x_left + trim_ratio, 1.0)
      final_image = an_image.execute_transforms()
    elif current_aspect_ratio < required_aspect_ratio:
      #resize width, crop height
      an_image.resize(width = required_width)
      an_image.execute_transforms()
      trim_ratio = float(required_height) / float(an_image.height)
      y_top = (1.0 - trim_ratio) / 2.0
      an_image.crop( 0.0, y_top, 1.0, y_top + trim_ratio)
      final_image = an_image.execute_transforms()
    else:
      an_image.resize(width = required_width, height = required_height)
      final_image = an_image.execute_transforms()
    self.response.headers['Content-Type'] = "image/jpeg"
    self.response.out.write(final_image)

class AddGuitar(webapp.RequestHandler):
    def get(self):
        if users.get_current_user():
            path = os.path.join(os.path.dirname(__file__), 'templates/addguitar.html')
            self.response.out.write(template.render(path, ""))
        else:
            self.redirect(users.create_login_url(self.request.uri))
    def post(self):
        if users.get_current_user():
            #TODO add form validation - just make it quick and dirty for now
            guitar = Guitars()
            #first, the easy request items
            guitar.name = self.request.get('guitarname')
            #now the images
            theimage = self.request.get("guitarimage")
            guitar.image = db.Blob(theimage)
            #our random number so we can get a random guitar
            guitar.rand = random.random() 
            guitar.put()
            self.redirect('/add-guitar')
        else:
            self.redirect('/')

class About(webapp.RequestHandler):
    def get(self, trailingurl = None):
      path = os.path.join(os.path.dirname(__file__), 'templates/about.html')
      self.response.out.write(template.render(path, ""))


class Index(webapp.RequestHandler):
    def get(self, trailingurl = None):
      path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
      self.response.out.write(template.render(path, ""))

application = webapp.WSGIApplication(
                                     [('/add-guitar', AddGuitar),
                                      (r'/(\d+)/(\d+)/?', GetGuitarImage),
                                      ('/about', About),
                                      ('/.*', Index),],
                                     debug=True)
def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
