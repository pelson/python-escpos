from escpos import printer

import contextlib

@contextlib.contextmanager
def contextual_formatting(printer, start, end):
   try:
      printer._raw(start)
      yield
   finally:
      printer._raw(end)

import functools
underline = functools.partial(contextual_formatting, start='\x1b\x2d1', end='\x1b\x2d0')
bold = functools.partial(contextual_formatting, start='\x1b\x451', end='\x1b\x450')
large = functools.partial(contextual_formatting, start='\x1d\x21\x01', end='\x1d\x21\x00')
inverted = functools.partial(contextual_formatting, start='\x1d\x421', end='\x1d\x420')
linespacing_24 = functools.partial(contextual_formatting, start='\x1B\x33' + chr(24), end='\x1B\x32')
align_right = functools.partial(contextual_formatting, start='\x1B\x61' + chr(2), end='\x1B\x61' + chr(0))
align_center = functools.partial(contextual_formatting, start='\x1B\x61' + chr(1), end='\x1B\x61' + chr(0))

Epson = printer.Serial("/dev/ttyUSB0")

Epson.control('FW')

Epson._raw('\x10\x04' + chr(2))
#bytes = (ord(b) for b in Epson.device.read(1))
#for b in bytes:
#    for i in xrange(8):
#       print (b >> i) & 1
#exit()


#Epson.barcode('1324354657687','EAN13',64,2,'','')
#with inverted(Epson):
#    Epson.text("Hello world")
#Epson._raw('\x1b\x2d1')
#with underline(Epson), bold(Epson), large(Epson):
#    Epson.text('Hello world')

def draw_image(image_array, horizontal_density, vertical_density, x_pos=0):
    """
    Generator which successively sends 1/15th of an inch in the vertical of the given image
    (at the given dpi). After each iteration a newline of height 24 pixels must be sent
    before the next section of the image can be drawn. E.g:

        with linespacing_24(Epson):
            Epson.control('LF')

    """
    W = image_array.shape[1]
    nH = W // 256
    nL = W % 256
    if vertical_density == 180 and horizontal_density == 180:
        m = 33
    elif vertical_density == 180 and horizontal_density == 90:
        m = 32
    elif vertical_density == 60 and horizontal_density == 180:
        m = 1
    elif vertical_density == 60 and horizontal_density == 90:
	m = 0
    else:
        raise ValueError('Unsupported mode.')

    if m in [0, 1]:
        band_size = 8
    else:
        band_size = 24

    bin_powers = 2 ** np.arange(8)[::-1, np.newaxis]

    # For each band of 1/15th of an inch (at either 60 or 180 
    # vertical pixels per inch) transmit the image data and pass
    # context back so that other things can be drawn on each
    # successive line.
    for band in range(0, image_array.shape[0], band_size):
        # Move the x position to the given location for each band.
        set_absolute_print_position(x_pos, 0)
	Epson._raw('\x1b\x2a' + chr(m) + chr(nL) + chr(nH))
        for i in range(W):
            upper = min([image_array.shape[0], band + band_size])
            full_band = np.zeros(band_size, dtype=np.bool)
            full_band[:(upper - band)] = (image_array[band:upper, i] == 0)
            full_band = full_band.reshape(band_size//8, 8).T
            byte_vals = (bin_powers * full_band).sum(axis=0)
            for byte_val in byte_vals:
                Epson._raw(chr(byte_val))	
	yield
        

import numpy as np
import PIL.Image
PIL.Image.open('simple_logo_raster.gif').convert('1').save('simple_logo_raster_bw.gif')
data = np.array(PIL.Image.open('simple_logo_raster_bw.gif'))
data = np.array(PIL.Image.open('simple_logo_raster.gif')) != 0
print data.dtype, data.max(), data.shape
#draw_image(data, 90, 60)
#for band in draw_image(data, 90, 60):
#    Epson.text('next line')
#draw_image(data, 90, 180)
#draw_image(data, 90, 180)
#draw_image(data, 180, 180)


def set_absolute_print_position(x, y):
    Epson._raw('\x1b\x24' + chr(x) + chr(y))

def draw_code39(code, height=20, width=3):
    code = str(code)
    # Barcode height.
    Epson._raw('\x1d\x68' + chr(height))
    # Barcode width.
    Epson._raw('\x1d\x77' + chr(width))
    # Font position
    Epson._raw('\x1d\x48' + chr(0))
    # Font HRI
    Epson._raw('\x1d\x66' + chr(1))

    mode_2 = True
    if mode_2:
        Epson._raw('\x1d\x6b' + chr(67) + chr(len(code)))
    else:
        Epson._raw('\x1d\x6b' + chr(2))# + chr(len(code)))
    Epson._raw(code)
    if not mode_2:    
       Epson._raw(chr(0))

def print_and_feed(n):
    Epson._raw('\x1B\x64' + chr(n))



#set_absolute_print_position(0, 0)

#draw_code39(496595707379)
#Epson.text('before?')
#Epson.cut()
#for _ in draw_image(data, 180, 180, x_pos=100):
#    with linespacing_24(Epson):
#        Epson.control('LF')
#Epson.cut()
#exit()
#import matplotlib.pyplot as plt

#import barcode
#from barcode.writer import ImageWriter
#EAN = barcode.get_barcode_class('ean13')
#writer = ImageWriter()
#writer.set_options(dict(quiet_zone=0, dpi=180, font_size=0))
#an = EAN(u'5901234123457', writer=writer)
#fullname = ean.save('ean13_barcode')
#plt.imshow(plt.imread(fullname))
#plt.show()
#exit()

# barcode -b "hello" -n -e code39 -E | convert -density 180 - -trim -filter box -resize 54x -flatten -fill '#FFFFFF' -trim test.png

#barcode = np.array(PIL.Image.open('test.png')).T != 0
#import matplotlib.pyplot as plt
#plt.imshow(barcode)
#plt.show()
#exit()
#print barcode.shape

import itertools
#for line, band in enumerate(itertools.izip_longest(draw_image(data, 90, 60), draw_image(barcode, 180, 180, x_pos=100))):
for line, band in enumerate(draw_image(data, 90, 60)):
    if line == 1:
        Epson.text('Hello world')
    elif line == 2:
        with inverted(Epson):
            with align_center(Epson):
                Epson.text("Hello world")
    elif line == 3:
        #Epson._raw('\x1d\x6b\x04')
        #Epson._raw('12345')
        #Epson.barcode('1324354657687','EAN13',64,2,'','')
        #Epson.text('foobar')
#        draw_code39(123456789012)
        pass
    elif line == 5:
        Epson.text('Visit us at: ')
    elif line == 6:
        with inverted(Epson):
            Epson.text("www.lazy-daisy.co.uk")
    else:
        print line

    with linespacing_24(Epson):
        Epson.control('LF')

with align_center(Epson):
#    Epson.text('496595707379')
    draw_code39(496595707379, height=30, width=3)
#Epson._raw(data.astype(np.ubyte).tostring())
#Epson.cut()
Epson.cashdraw(2)

#Epson.qr('foobar')
#Epson.image('simple_logo_raster.gif')

