from kivy.config import Config
Config.set('graphics', 'width', '960')
Config.set('graphics', 'height', '540')
#Config.set('graphics', 'fullscreen','auto')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image
from kivy.uix.video import Video
from kivy.clock import Clock

import filetype
import os

class MyVideo(Video):

    def on_eos(self, *args):
        # Go to the next screen
        if self.eos:
            self.parent.manager.next()
            
    def on_loaded(self, *args):
        if self.loaded == True:
            self.opacity = 1

    def __init__(self, **args):
        super(MyVideo, self).__init__(**args)

class MyImage(Image):

    def __init__(self, **args):
        super(MyImage, self).__init__(**args)        

class VideoScreen(Screen):

    def on_pre_enter(self):
        self.media.source = self.source_file
        self.media.eos = False
        self.media.state = 'play'
        
    def on_leave(self):
        self.media.opacity = 0
        self.media.unload()
        self.media.source = ''
        self.media.loaded = False

    def __init__(self, file, **args):
        super(VideoScreen, self).__init__(**args)
        self.source_file = file
        self.media = MyVideo(source=file, state='stop', options={'eos': 'stop'})
        self.add_widget(self.media)
    

class ImageScreen(Screen):

    def on_pre_enter(self):
        self.media.reload()

    def on_enter(self):
        Clock.schedule_once(self.manager.next, self.manager.image_duration)

    def __init__(self, file, **args):
        super(ImageScreen, self).__init__(**args)
        self.media = MyImage(source=file, nocache=True)
        self.add_widget(self.media)    

class ScreenManagement(ScreenManager):

    screen_index = 0
    media_path = './'
    image_duration = 3.
    
    def next(self, *args):
        # Function to advance to the next screen
        self.screen_index += 1
        if self.screen_index >= len(self.screens):
            self.screen_index = 0
        print('going to screen: ' + str(self.screen_index))
        if self.current != self.sorted_names[self.screen_index]:
            self.current = self.sorted_names[self.screen_index]
        else:
            self.next() # Uh oh, somehow we're ending up with two of the same slide

    def find_items(self, dt, startup=False, *args):
    
        # Function to search the media directory for files to display
        print('Checking the directory...')

        files = os.listdir(self.media_path)
        sorted_names = None # Holds the sorted version of self.screen_names
        
        for file in files:
            if file not in self.screen_names: # This is a new screen
            
                try: # If we have a directory, filetype.guess will throw an error
                    kind = filetype.guess(self.media_path+file).mime
                except PermissionError:
                    print('Directory ' + file + ' ignored')
                except AttributeError:
                    pass
                else:               
                    if kind[0:5] == 'video':
                        screen = VideoScreen(self.media_path+file, name=file)
                        self.add_widget(screen)
                    elif kind[0:5] == 'image':
                        screen = ImageScreen(self.media_path+file, name=file)
                        self.add_widget(screen)
                    else:
                        print('Unsupported filetype: ' + kind + ' (' + file + ')')
                    
        for name in self.screen_names: # remove old screens
            if name not in files:
                self.remove_widget(self.get_screen(name))
                print('removed: ' + name)
        self.sorted_names = sorted(self.screen_names)
        if startup:
            self.current = self.sorted_names[self.screen_index]
        else:
            self.refresh_config()

    def get_config(self):
        # Function to parse arguments from a configuration file
        # dt passed by clock. We ignore it

        with open('config.conf', 'r') as f:
            for line in f:

                line = line.split('#',1)[0] # Check for comment symbol (#)

                if line[0:15].lower() == 'image_duration:': # How long to display each image
                    self.image_duration = int(line[15:].strip())
                if line[0:15].lower() == 'media_location:': # Where the media is stored
                    self.media_path = line[15:].strip()

    def refresh_config(self):
        # Function to reread the configuration file and force widget refreshes

        # Read variables from the config file
        self.get_config()

           
    def __init__(self):
        super(ScreenManagement, self).__init__()
        self.get_config()
        self.find_items('',startup=True)
        Clock.schedule_interval(self.find_items, 6.) # Once per minute          

class MainApp(App):
    def build(self):
        self.manager = ScreenManagement()
        return(self.manager)

MainApp().run()