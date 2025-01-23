from PIL import Image
import numpy as np
import scipy.io.wavfile as wave

SAMPLE_RATE = 44100*8
SYNC_PULSE = 1200
SYNC_PORCH = 1500
MIN_FREQ = 1500
MAX_FREQ = 2300



class SSTV:

    @staticmethod
    def generate_vawe(freq,dur,phase = 0):
        w = np.linspace(0,dur,int(SAMPLE_RATE*dur),endpoint= False)
        return np.sin(2 * np.pi * freq * w + phase)
    
    @staticmethod
    def generate_line_signal(line_data,line_dur):
        line = np.zeros(int(SAMPLE_RATE*line_dur))
        pixel_dur = line_dur/len((line_data))
        phase = 0
        for i in range(len(line_data)):
            pixel_sample = int(pixel_dur * SAMPLE_RATE)
            start = i*pixel_sample
            end = start + pixel_sample
            frequencies = MIN_FREQ + (line_data[i]/255)* (MAX_FREQ - MIN_FREQ)
            line[start:end] = SSTV.generate_vawe(frequencies,pixel_dur,phase)

            phase += (2 * np.pi * frequencies * pixel_dur) % (2 * np.pi)
            
        return line
    
    @staticmethod
    def header_vis(vis_code):
        header = []

        # calibration header
        header.append(SSTV.generate_vawe(1900,0.3))
        header.append(SSTV.generate_vawe(1200,0.01))
        header.append(SSTV.generate_vawe(1900,0.3))

        header.append(SSTV.generate_vawe(1200,0.03)) #start bit

        vis_bit = "{0:07b}".format(vis_code)
        for bit in reversed(vis_bit):

            if bit == "0":
                header.append(SSTV.generate_vawe(1300,0.03))
            elif bit == "1":
                header.append(SSTV.generate_vawe(1100,0.03))

        #even parity bit
        if (vis_bit.count("1") % 2) == 0:
            header.append(SSTV.generate_vawe(1300,0.03)) 
        else:
            header.append(SSTV.generate_vawe(1100,0.03)) 
        header.append(SSTV.generate_vawe(1200,0.03)) # stop bit

        return header
    
    class Scottie1:
        def __init__(self):      
            self.LINE_SYNC_PULSE_DUR = 0.009
            self.SYNC_PORCH_DUR = 0.0015 
            self.line_dur = 0.1382440    

        def encode(self,image):
            audio = []

            audio.extend(SSTV.header_vis(60))
            audio.append(SSTV.generate_vawe(SYNC_PULSE,self.LINE_SYNC_PULSE_DUR))

            for line in image:
                audio.append(SSTV.generate_vawe(SYNC_PORCH,self.SYNC_PORCH_DUR))
                
                for i in [1,2,0]:
                    audio.append(SSTV.generate_line_signal(line[:,i],self.line_dur))
                    if i == 2:
                        audio.append(SSTV.generate_vawe(SYNC_PULSE,self.LINE_SYNC_PULSE_DUR))
                    if i!=0:
                        audio.append(SSTV.generate_vawe(SYNC_PORCH,self.SYNC_PORCH_DUR))
                        

            return np.concatenate(audio)
        
    class Robot36:
        def __init__(self):
            self.LINE_SYNC_PULSE_DUR = 0.009
            self.SYNC_PORCH_DUR = 0.003
            self.line_dur = 0.088

        def encode(self,image):
            audio = []

            audio.extend(SSTV.header_vis(8))

            for i in range(len(image)):

                audio.append(SSTV.generate_vawe(SYNC_PULSE,self.LINE_SYNC_PULSE_DUR))
                audio.append(SSTV.generate_vawe(SYNC_PORCH,self.SYNC_PORCH_DUR))
                audio.append(SSTV.generate_line_signal(image[i,:,0],self.line_dur))

                if ((i) % 2 )== 0:
                    audio.append(SSTV.generate_vawe(1500,0.0045))
                    audio.append(SSTV.generate_vawe(1900,0.0015))
                    audio.append(SSTV.generate_line_signal(image[i,:,2],0.044))
                else:
                    audio.append(SSTV.generate_vawe(2300,0.0045))
                    audio.append(SSTV.generate_vawe(1900,0.0015))
                    audio.append(SSTV.generate_line_signal(image[i,:,1],0.044))

    

            return np.concatenate(audio)



                    
                    
        


a = Image.open(r"Image.jpg").resize((320,240))
a = np.array(a.convert("YCbCr"))

print(a.shape)
encoded = SSTV.Robot36().encode(a)
encoded = (encoded / np.max(np.abs(encoded)) * 32767).astype(np.int16)

wave.write("output.wav",SAMPLE_RATE,encoded)

