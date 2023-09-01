import time
from spiro.logger import log, debug

class OldCamera:
    def __init__(self):
        debug('Legacy camera stack detected.')
        self.camera = PiCamera()
        self.type = 'legacy'
        # cam.framerate dictates longest exposure (1/cam.framerate)
        cam.framerate = 5
        cam.iso = 50
        cam.resolution = self.camera.MAX_RESOLUTION
        cam.rotation = 90
        cam.image_denoise = False
        self.cam.meter_mode = 'spot'

    def start_stream(self, output):
        self.camera.resolution = "2592x1944"
        self.camera.start_recording(output, format='mjpeg', resize='1024x768')

    def stop_stream(self):
        self.camera.stop_recording()
        self.camera.resolution = self.camera.MAX_RESOLUTION

    @property
    def zoom(self):
        return self.camera.zoom

    def set_zoom(self, x, y, w, h):
        self.camera.zoom = (x, y, w, h)
    
    def auto_exposure(self, value):
        if value:
            self.camera.shutter_speed = 0
            self.camera.exposure_mode = "auto"
            self.camera.iso = 0
        else:
            self.camera.exposure_mode = "off"

    def capture(self, obj, format='png'):
        self.camera.capture(obj, format=format)

    @property
    def shutter_speed(self):
        return self.camera.shutter_speed

    @property
    def iso(self):
        return self.camera.iso
    
    @iso.setter
    def iso(self, value):
        self.camera.iso = value
    
    def close(self):
        self.camera.close()



class NewCamera:
    def __init__(self):
        debug('Libcamera detected.')
        self.camera = Picamera2()
        self.type = 'libcamera'
        self.streaming = False
        self.stream_output = None
        self.still_config = self.camera.create_still_configuration(main={"size": (4608, 3456)}, lores={"size": (320, 240)})
        self.video_config = self.camera.create_video_configuration(main={"size": (1024, 768)})
        self.camera.configure(self.video_config)
        self.lens_limits = self.camera.camera_controls['LensPosition']

        self.camera.set_controls({'NoiseReductionMode': controls.draft.NoiseReductionModeEnum.Off,
                                      'AeMeteringMode': controls.AeMeteringModeEnum.Spot,
                                      "AfMode": controls.AfModeEnum.Manual, 
                                      "LensPosition": self.lens_limits[2]})
        self.camera.start()

    def start_stream(self, output):
        log('Starting stream.')
        try:
            self.stream_output = output
            self.streaming = True
            self.camera.switch_mode(self.video_config)
            self.camera.start_recording(MJPEGEncoder(), FileOutput(output))
        except:
            pass

    def stop_stream(self):
        # we do not want to stop the stream on libcamera, since it can switch modes without doing so.
        pass

    @property
    def zoom(self):
        return None # XXX

    def set_zoom(self, x, y, w, h):
        '''libcamera wants these values in pixels whereas the legacy stack wants values as fractions.'''
        (resx, resy) = self.camera.camera_properties['PixelArraySize']
        self.camera.set_controls({"ScalerCrop": [int(x * resx), int(y * resy), int(w * resx), int(h * resy)]})
        print({"ScalerCrop": [int(x * resx), int(y * resy), int(w * resx), int(h * resy)]})

    def reset_zoom(self):
        self.camera.set_controls({"ScalerCrop": [0, 0, *self.camera.camera_properties['PixelArraySize']]})
    
    def auto_exposure(self, value):
        self.camera.set_controls({'AeEnable': value})

    def capture(self, obj, format='png'):
        stream = self.streaming

        log('Capturing image.')
        self.camera.switch_mode(self.still_config)
        self.camera.capture_file(obj, format=format)
        log('Ok.')

        if stream:
            self.start_stream(self.stream_output)

    @property
    def shutter_speed(self):
        return self.camera.capture_metadata()['ExposureTime']
    
    @shutter_speed.setter
    def shutter_speed(self, value):
        self.camera.set_controls({"ExposureTime": value})

    @property
    def iso(self):
        return int(self.camera.capture_metadata()['AnalogueGain'] * 100)
    
    @iso.setter
    def iso(self, value):
        self.camera.set_controls({"AnalogueGain": value / 100})

    def close(self):
        self.camera.close()

    def still_mode(self):
        self.camera.stop_encoder()
        self.camera.switch_mode(self.still_config)

    def video_mode(self):
        self.camera.stop_encoder()
        self.camera.switch_mode(self.video_config)

    @property
    def resolution(self):
        # XXX
        return (4608, 3456)

    @resolution.setter
    def resolution(self, res):
        # XXX
        pass

    @property
    def awb_mode(self):
        # XXX: not implemented
        pass
    
    @awb_mode.setter
    def awb_mode(self, mode):
        # XXX: not implemented
        pass

    @property
    def awb_gains(self):
        # XXX: not implemented
        pass
    
    @awb_gains.setter
    def awb_gains(self, gains):
        # XXX: not implemented
        pass
    
    def focus(self, val):
        self.camera.set_controls({'LensPosition': val})


try:
    from picamera import PiCamera
    try: cam
    except NameError: cam = OldCamera()
except:
    from picamera2 import Picamera2
    from picamera2.outputs import FileOutput
    from picamera2.encoders import MJPEGEncoder
    from libcamera import controls
    try: cam
    except NameError: cam = NewCamera()

