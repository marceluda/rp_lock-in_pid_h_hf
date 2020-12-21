# -*- coding: utf-8 -*-
"""
Created on Wed Nov  8 16:53:16 2017

@author: lolo
"""


from numpy import *
import matplotlib.pyplot as plt

#%%

import glob
import subprocess
from datetime import datetime
import struct
import time

import struct

def smooth(x, window_len=11, window='hanning'):
    s=r_[2*x[0]-array(x[window_len:1:-1]), x, 2*x[-1]-array(x[-1:-window_len:-1])]
    w = ones(window_len,'d')
    y = convolve(w/w.sum(), s, mode='same')
    return y[window_len-1:-window_len+1]

def lta_find_head(filename):
    with open(filename, 'r') as file:
        i=0
        for line in file:
            i+=1
            if re.search('^Time[ ]*\[ms\]\t',line,re.M):
                break
    return i

def findpeaks(x,minh=0,mind=1):
    nn=len(x)
    z=nonzero(
        logical_and(
            logical_and( 
                diff(x)[0:nn-2]*diff(x)[1:nn-1]<=0 ,
                diff(x)[0:nn-2]>0
                ),
            x[0:nn-2]>minh
            )
        )[0]+1
    z=z.tolist()
    while(len(nonzero(diff(z)<mind)[0])>0):
        z.pop( nonzero(diff(z)<mind)[0][0]+1 )
    return z

def goodYlim(yy,margin=0.1,offset=0):
    full_range=max(yy)-min(yy)
    gmin=min(yy)-full_range*margin/2 + min(0,offset)*full_range
    gmax=max(yy)+full_range*margin/2 + max(0,offset)*full_range
    return (gmin,gmax)

def now():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
    except TypeError:
        return False

today=datetime.now().strftime("%Y%m%d")



class read_dump():
    """
    This class is a toolkit to read .bin files generated by red_pitaya_lock() streaming
    functions.
    
    Example:
    d = read_dump(filename='/path/file.bin', head1_size=100, head2_size=3400 )
    
    This creates d object that lets you processes the streamead data.
    The first 100 bytes have information about the starting time of the streaming and
    the streamed reg names.
    The next 3400 bytes have information about the lock regs in FPGA at the time of
    streaming start. Both numbers can be changed for special situatiosn using head1_size
    and head2_size params.
    
    
    
    Usage:
        d.load_params()     # loads regs values from self.filename headers
        d.load_range()      # loads a range of values by index position
        d.load_time()       # loads a range of values by time position
        d.plot()            # Plots a loaded range
        d.plotr()           # Loads a range of values by index and plots
        d.plott()           # Loads a range of values by time and plots
        d.fast_plotr()      # Fast plot by index range
        
        d.time_stats()      # Calcs useful time statistical information
        d.allan_range()     # Calcs Allan deviation of a data set selected by index range
        d.allan_range2()    # Calcs Allan deviation of a data set selected by index range
                            # with a heavier algorithm that takes care of error intervals
        
        d.save_buff()       # Saves allan_dev data and time_stats data in a file
        d.load_buff()       # Loads allan_dev data and time_stats data in a file
        d.export_range()    # Exports data to a text file
        d.print_t0()        # Prints data adquisition start time
        
        d.plot_allan()      # Plots allan deviation
        d.plot_allan_error  # Plots allan deviation with error intervals
        
        
    
    """
    def __init__(self,filename,head1_size=100,head2_size=3400):
        self.filename   = filename
        self.head1_size = head1_size
        self.head2_size = head2_size
        self.head_size  = head1_size+head2_size
        self.load_params()
        self.plotlim    = 1000000
        self.data       = array([])
        self.newfig     = True
        self.allan      = []
        self.locked_ranges = []
        self.time_stats_data = {}
        self.t          = []
        self.t0         = datetime.fromtimestamp( float([ y.split(' ')[-1] for y in filter(lambda x: 'timestamp' in x , self.txt1.decode().split('\n') ) ][0]))
        
    def load_params(self):
        """
        Reads self.filename and gets header information. 
        
        Usage:
            d.load_params()
        
        Headers texts are stored in self.txt .
        The text is processed and the params keys and values of RP lock module memory regs
        are stored in self.params as a Dictionary.
        The names for the signals sotred in the .bin file are stored in self.names .
        Labels for plots are stored in dself.ylbl
        
        Example:
            d=read_dump(filename='/home/lolo/data/20171109_184719.bin')
            d.load_params()
            
            print(d.params['error_offset'])
        
        """
        with open(self.filename,'rb') as f:
            txt1=f.read(self.head1_size)
            txt2=f.read(self.head2_size)
        txt=txt1+txt2
        N=len(txt.decode().split('\n')[0].split(','))
        self.strstr='!f'+'l'*N
        self.ylbl=txt1.decode().split('\n')[0].split(' ')[1].split(',')
        self.names=['t']
        self.names.extend(self.ylbl)
        self.txt1=txt1
        self.params={}
        for i in txt2.decode().split('{')[1].split('}')[0].replace('\n','').split(','):
            if len(i)>2:
                self.params[i.split(':')[0].split('"')[1]]=float(i.split(':')[1])
    
    def __getitem__(self, key):
        if type(key)==int:
            return self.data[key]
        if type(key)==str:
            return self.data[self.names.index(key)]
        if type(key)==slice:
            return self.data[key]
        
    def print_t0(self):
        """
        Prints data adquisition start time read from .bin fiel
        Example:
             d=read_dump(filename='/home/lolo/data/20171109_184719.bin')
             d.print_t0()
             20171109_18:47:20
        
        """
        print(self.t0.strftime('%Y%m%d_%H:%M:%S'))
        
    def load_range(self,start=0,end=-1,large=None,step='auto'):
        """
        Loads data from .bin filename and stores it in numpy arrays for data processing and plotting.
        Each data bin consist in the measurement time and several signals values.
        The signals names are the self.names ones.
        The data loaded is filtered by and start index an stop index, where the index is the bin number.
        After loadding the data, several arrays with independent signals are set:
            self.t           : time array
            self.n           : index array
            self.SIGNAL_NAME : for each signal read, one adata array is set.
        
        Usage:
            self.load_range(start=0,end=-1,large=None,step='auto')
            
        Params:
            start : Start position of the data to read
            stop  : Stop position of the data to read
            step  : step size in number of bins between data. step==1 means no jumps.
            large : if defined, data reading is stopped after getting 'large' data points.
            
        After succesfully reading the data, its stored in self.data. 
        
        Example:
             d=read_dump(filename='/home/lolo/data/20171109_184719.bin')
             d.load_range(start=1000,end=5000,step=1)
             print( std( d.error ) )
             plt.plot( d.t , d.oscA ) 
             
        """
        self.check_time_stats()
        autoset=False
        if end<0:
            end=self.time_stats_data['data_length']-end
            autoset=True
        if not is_int(step):
            step=int(max(1, 10**floor(log10( end-start )-4) ))
            autoset=True
        if autoset:
            print('autoset: end={:d}, step={:d}'.format(end,step))
        
        large_break = is_int(large);
        
        tbuff=time.time()
        with open(self.filename,'rb') as f:
            f.read(self.head_size)
            cs=struct.calcsize(self.strstr)
            if start>1:
                f.read(cs*start)
            fc=f.read(cs)
            j=start
            data=[]
            while fc:
                if j % step==0:
                    data.append( [j]+ list(struct.unpack(self.strstr,fc)) )
                fc=f.read(cs)
                j+=1
                if round((j-start)/step)>self.plotlim:
                    print('ERROR: data length exeded {:d} points'.format(self.plotlim))
                    break
                if j>=end:
                    break
                if large_break and round((j-start)/step)>large:
                    break
        print('Load time: {:f} sec'.format( time.time()-tbuff ))
        self.data=array(data)
        for i,n in enumerate(['n']+self.names):
            setattr(self,n,self.data[:,i])
    
    def load_time(self,start=0,end=-1,large=None,step='auto'):
        """
        Loads data from .bin filename and stores it in numpy arrays for data processing and plotting.
        Each data bin consist in the measurement time and several signals values.
        The signals names are the self.names ones.
        The data loaded is filtered by an start time and stop time, where the time is in seconds.
        After loadding the data, several arrays with independent signals are set:
            self.t           : time array
            self.n           : index array
            self.SIGNAL_NAME : for each signal read, one adata array is set.
        
        Usage:
            self.load_time(start=0,end=-1,large=None,step='auto')
            
        Params:
            start : Start time of the data to read
            stop  : Stop time of the data to read
            step  : step size in number of bins between data. step==1 means no jumps.
            large : if defined, data reading is stopped after getting 'large' seconds of data points.
            
        After succesfully reading the data, its stored in self.data. 
        
        Example:
             d=read_dump(filename='/home/lolo/data/20171109_184719.bin')
             d.load_time(start=60*5,end=60*15,step=1)
             print( std( d.error ) )
             plt.plot( d.t , d.oscA ) 
             
        """
        self.check_time_stats()
        if end==None and large==None:
            print('needs start + end|large')
            return
        end_break   = is_int(end);
        large_break = is_int(large);
        
        self.check_time_stats()
        autoset=False
        if end<0:
            end=self.time_stats_data['last_time']-end
            autoset=True
        if not is_int(step):
            dl=int(( end-start )/self.time_stats_data['last_time']*self.time_stats_data['data_length'])
            step=int(max(1, 10**floor(log10( dl )-4) ))
            autoset=True
        if autoset:
            end,step = int(end),int(step)
            print('autoset: end={:d}, step={:d}'.format(end,step))
        
        large_break = is_int(large);
        
        tbuff=time.time()
        with open(self.filename,'rb') as f:
            f.read(self.head_size)
            cs=struct.calcsize(self.strstr)
            fc=f.read(cs)
            j=0
            j0=0
            data=[]
            save_data=False
            while fc:
                tnow=struct.unpack(self.strstr,fc)[0]
                if save_data==False and tnow>start:
                    save_data=True
                    j0=j
                if save_data and (j-j0) % step==0:
                    data.append( [j]+ list(struct.unpack(self.strstr,fc)) )
                fc=f.read(cs)
                j+=1
                if round((j-j0)/step)>self.plotlim:
                    print('ERROR: data length exeded {:d} points'.format(self.plotlim))
                    break
                if end_break and tnow>=end:
                    break
                if large_break and tnow-start>large:
                    break
        print('Load time: {:f} sec'.format( time.time()-tbuff ))
        self.data=array(data)
        print('Data length: {:d}'.format( len(self.data) ) )
        for i,n in enumerate(['n']+self.names):
            setattr(self,n,self.data[:,i])
    

    def plot_from_range(self):
        rr=array(plt.ginput(2)).astype(int)[:,0]
        step=max(1, 10**floor(log10( abs(diff(rr)) ) -4) )
        if type(step)==ndarray:
            step=step[0]
        print('step='+str(step))
        self.plotr(signals=self.last_signals,start=min(rr),end=max(rr),step=step)    
    
    def get_index(self,n=1):
        ind=array(plt.ginput(n)).astype(int)[:,0].tolist()
        for i in ind:
            print('index: '+str(i))
        return ind
    
    def plot(self,signals,figsize=(12,5),time=True,relative=False,autotime=True):
        """
        Plots loaded data.
        
        Usage:
            self.plot(signals,figsize=(12,5),time=True,relative=False,autotime=True)
            
        Params:
            signals  : space separated string or a list with signals names to plot
            figsize  : size of figure windows
            time     : if True, x axis is in time units. Else, in index [int] units
            relative : if True, x axis starts at zero, else use absolute value for time/index
            autotime : If True, x axis units are set in human readble most useful units.
                    
        Example:
             d=read_dump(filename='/home/lolo/data/20171109_184719.bin')
             d.load_time(start=60*5,end=60*15,step=1)
             d.plot( 'error' ) 
             
        """
        if type(signals)==str:
            signals=signals.split(' ')
        for i in signals:
            if not i in self.names[1:]:
                print(i+' is not in names')
                return False
        if self.newfig:
            plt.figure(figsize=figsize)
        else:
            plt.clf()
        self.last_signals=signals
        self.ax=[]
        self.ax.append( plt.subplot2grid( (len(signals),1), (0, 0))  )
        for i in range(1,len(signals)):
            self.ax.append( plt.subplot2grid( (len(signals),1), (i, 0), sharex=self.ax[0])  )
        if len(self.t)==0:
            print('needs tu run load_range first')
            return False
        xlbl='seg'
        xx=self.t
        xx_len=max(xx)-min(xx)
        if time:
            xlbl='time [sec]'
            if autotime and max(abs(xx)) < 5e-4:
                xx=xx*1e6
                xlbl='time [us]'
            elif autotime and max(abs(xx)) < 5e-1:
                xx=xx*1e3
                xlbl='time [ms]'
            elif autotime and xx_len > 60*5 and max(abs(xx)) <= 60*60*3 :
                xx=xx/60
                xlbl='time [min]'
            elif autotime and xx_len > 60*60*3 :
                xx=xx/60/60
                xlbl='time [hour]'
        else:
            xx=self.n
            xlbl='int'
        if relative:
            xx=xx-xx[0]
        for i,signal in enumerate(signals):
            self.ax[i].plot( xx , getattr(self,signal), linewidth=0.5 )
            self.ax[i].grid(b=True)
            self.ax[i].set_ylabel(signal)
        self.ax[-1].set_xlabel(xlbl)
        if autotime and ( ('min' in xlbl) or ('sec' in xlbl) ) :
            t0,t1=self.ax[-1].get_xlim()
            self.ax[-1].set_xticks( arange( ceil(t0/60)*60 , floor(t1/60)*60+60 , 60 ) )
            self.ax[-1].set_xlim( (t0,t1))
            
        plt.tight_layout()
    
    def plott(self,signals,start=0,end=-1,large=None,step='auto',relative=False):
        self.load_time(start=start,end=end,large=large,step=step)
        self.plot(signals=signals,time=True,relative=relative)
    def plotr(self,signals,start=0,end=-1,large=None,step='auto',relative=False):
        self.load_range(start=start,end=end,large=large,step=step)
        self.plot(signals=signals,time=False,relative=relative)
    
    def fast_plotr(self,signals,index=10000,large=10000,relative=False):
        self.plotr(signals,start=int(index-large/2),end=int(index+large/2),relative=relative )
    
    def time_stats(self):
        """
        Calculates time statistics data
        
        Usage:
            self.time_stats())
             
        """
        tbuff=time.time()
        with open(self.filename,'rb') as f:
            f.read(self.head_size)
            cs=struct.calcsize(self.strstr)
            fc=f.read(cs)
            j=0
            data=[]
            # first read
            tnow  = struct.unpack(self.strstr,fc)[0]
            tlast = struct.unpack(self.strstr,fc)[0]
            fc=f.read(cs)
            max_dt=0
            min_dt=1e100
            j=1
            while fc:
                tlast=tnow
                tnow=struct.unpack(self.strstr,fc)[0]
                max_dt=max(max_dt,tnow-tlast)
                if tnow-tlast>0:
                    min_dt=min(min_dt,tnow-tlast)
                fc=f.read(cs)
                j+=1
        print('Load time   : {:f} sec'.format( time.time()-tbuff ))
        print('Data length : {:d}'.format( j ) )
        print('Last time   : {:f} sec'.format( tnow ) )
        print('Max dt      : {:f} sec'.format( max_dt ) )
        print('Min dt      : {:f} sec'.format( min_dt ) )
        self.time_stats_data= { 'data_length':j , 'last_time': tnow, 'max_dt' :max_dt, 'min_dt':min_dt }

    def find_locked(self,error_signal=1,ctrl_signal=2):
        tbuff=time.time()
        with open(self.filename,'rb') as f:
            f.read(self.head_size)
            cs=struct.calcsize(self.strstr)
            j=0
            error_std=[0]*10
            ctrl_std =[0]*10
            locked=False
            self.locked_ranges=[]
            for i in range(9):
                fc=f.read(cs)
                error_std[i] = struct.unpack(self.strstr,fc)[error_signal]
                ctrl_std[i]  = struct.unpack(self.strstr,fc)[ctrl_signal]
                j+=1
            print(j)
            while fc:
                fc=f.read(cs)
                error_std[j%10] = struct.unpack(self.strstr,fc)[error_signal]
                ctrl_std[j%10]  = struct.unpack(self.strstr,fc)[ctrl_signal]
                #print( [j, std(error_std) , std(ctrl_std)] )
                if locked==False and ( std(error_std)<70 and std(ctrl_std)<500 ):
                    locked=True
                    self.locked_ranges.append( [j,-1] )
                if locked==True and ( std(error_std)>=70 or std(ctrl_std)>=500 ):
                    locked=False
                    self.locked_ranges[-1][1]=j
                    print(self.locked_ranges[-1])
                j+=1
        print('Load time: {:f} sec'.format( time.time()-tbuff ))
        self.locked_range= j
        
    def save_buff(self):
        """
        Saves data in file: self.filename+'_buff.npz'
        
        Usage:
            self.save_buff()
             
        """
        savez(self.filename.split('.')[0:-1][0]+'_buff.npz', 
              locked_ranges   = self.locked_ranges,
              time_stats_data = self.time_stats_data ,
              allan           = self.allan )
    
    def load_buff(self):
        """
        Loads data from file: self.filename+'_buff.npz'
        
        Usage:
            self.save_buff()
             
        """
        data=load(self.filename.split('.')[0:-1][0]+'_buff.npz')
        self.locked_ranges   = data['locked_ranges']
        self.time_stats_data = data['time_stats_data'].tolist()
        self.allan           = data['allan'].tolist()
    
    def print_locked_ranges(self):
        min_val=sort(diff(self.locked_ranges).flatten())[-10]-1
        for i,num in enumerate(diff(self.locked_ranges).flatten()):
            if num> min_val:
                print('j={:15d}:{:<15d} , large={:15d}'.format(
                        self.locked_ranges[i][0],
                        self.locked_ranges[i][1],
                        num ) )
                
    def export_range(self,signal,start=0,end=1,sp=0):
        """
        Exports data.
        
        Usage:
            self.export_range(signal,start=0,end=1,sp=0)
             
        """
        self.check_time_stats()
        s_ind=self.names.index(signal)
        max_dt_oom=floor(log10(self.time_stats_data['max_dt']))
        max_dt=ceil(self.time_stats_data['max_dt']*10**(-max_dt_oom))/10**(-max_dt_oom)
        print('Min time bin: {:f} sec'.format(max_dt))
        tbuff=time.time()
        time_already=False
        if len(self.allan)>0:
            for i in self.allan:
                if i['range']==[start,end]:
                    t0=i['t0']
                    t1=i['t1']
                    time_already=True
                    print('already have time info')
                    break
        if not time_already:
            with open(self.filename,'rb') as f:
                f.read(self.head_size)
                cs=struct.calcsize(self.strstr)
                fc=f.read(cs)
                j=0
                while fc:
                    tnow=struct.unpack(self.strstr,fc)[0]
                    if j==start:
                        t0=tnow
                    if j==end:
                        t1=tnow
                        break
                    fc=f.read(cs)
                    j+=1
        print('Load time: {:f} sec'.format( time.time()-tbuff ))
        print('t0: {:f} sec'.format( t0 ) )
        print('t1: {:f} sec'.format( t1 ) )
        print('Dt: {:f} sec | {:f} min'.format( t1-t0, (t1-t0)/60 ) )
        print('')
        bins_num=int(  floor(log( (t1-t0)/max_dt )/log(2)) -1 )
        print('Number of bins: {:d}'.format(bins_num))
        
        steps=max_dt
        v_s   = []
        v_tmp = []
        
        #v_lastmod  = 1e10
        v_lasttime = t0
        percentage      = '0%'
        percentage_step = int((end-start)/1000)
        j=0
        with open(self.filename,'rb') as f:
            with open(self.filename.split('.')[0:-1][0]+'_export_'+signal+'.dat', 'w') as output:
                f.read(self.head_size)
                cs=struct.calcsize(self.strstr)
                for j in range(start):
                    fc=f.read(cs)  
                    j+=1
                n=0
                while fc:
                    fc=f.read(cs)
                    vv=struct.unpack(self.strstr,fc)
                    tnow=vv[0]
                    if tnow > v_lasttime + steps:
                        v_lasttime=tnow
                        #v_s.append( mean( v_tmp ) )
                        output.write('{:>6d} {:15f}\r\n'.format(n, mean( v_tmp ) ) )
                        v_tmp=[ vv[s_ind] - sp   ]
                        n+=1
                    else:
                        v_tmp.append(  vv[s_ind] - sp  )
                    j+=1
                    if j>end:
                        break
                    if int((j-start))%percentage_step==0:
                        if not percentage == str(int((j-start)/(end-start)*100)) + '%':
                            percentage = str(int((j-start)/(end-start)*100)) + '%'
                            print( percentage )
        print('Total Load time: {:f} sec'.format( time.time()-tbuff ))
    
    def check_time_stats(self):
        """
        Check if time_stats  is done.
        
        Usage:
            self.check_time_stats()
             
        """
        if len(self.time_stats_data)==0:
            print('running first: self.time_stats()')
            self.time_stats()
            return False
        return True
    
    def plot_allan(self,num=-1):
        """
        Plots allan deviation of signals taken from allan_range
        Usage:
            self.plot_allan(num=-1)
        
        Params:
            num  : number of dataset to plot
        
        Example:
            d=read_dump(filename='/home/lolo/data/20171109_184719.bin')
            d.allan_range(start=6944, end=8148326,signal='error')
            d.allan[-1]['factor']= 1.5   # Factor multipliyed to signal before plotting
            d.plot_allan()
             
        """
        if len(self.allan)==0:
            print('Not allan data to plot')
            return False
        if num=='all':
            num=slice(0,len(self.allan))
        plt.figure()
        for i,aa in enumerate( self.allan[num] ):
            plt.loglog(aa['steps'],aa['allan_dev'],'o-',label=aa['signal'])
        plt.xlabel('time [sec]')
        plt.ylabel('Allan_dev [int]')
        plt.grid(b=True)
        plt.legend()
        plt.tight_layout()
    
    
    def plot_allan_error(self,num=-1,figsize=(12,5),bar=True):
        """
        Plots allan deviation of signals taken from allan_range2 with error intervals
        
        Usage:
            self.plot_allan_error(num=-1,figsize=(12,5),bar=True)
        
        Params:
            num     : number of dataset to plot or 'all'
            figsize : size of figure windows
            bar     : If True, express error intervals as error bars. Else, using color area.
            
        
        Example:
            d=read_dump(filename='/home/lolo/data/20171109_184719.bin')
            d.allan_range2(start=6944, end=8148326,signal='error')
            d.allan_range2(start=6944, end=8148326,signal='ctrl_A')
            d.allan[0]['factor']= 1.5   # Factor multipliyed to signal before plotting
            d.allan[1]['factor']= 100   # Factor multipliyed to signal before plotting
            d.plot_allan_error()
             
        """
        if len(self.allan)==0:
            print('Not allan data to plot')
            return False
        if num=='all':
            num=slice(0,len(self.allan))
        elif type(num)==int:
            num=slice(num,num+1)
        if self.newfig:
            plt.figure(figsize=figsize)
        else:
            plt.clf()
            
        self.ax=[]
        self.ax.append( plt.subplot2grid( (1,1), (0, 0))  )
        self.ax[-1].set_yscale('log')
        self.ax[-1].set_xscale('log')
        for i,aa in enumerate( self.allan[num] ):
            xx   = array(aa['steps'])
            yy   = array(aa['allan_dev'])*abs(aa['factor'])
            ymax = array(aa['allan_dev_max'])*abs(aa['factor'])
            ymin = array(aa['allan_dev_min'])*abs(aa['factor'])
            if bar:
                self.ax[-1].errorbar(xx, yy, yerr=[ yy-ymin , ymax-yy ] , fmt='.-',label=aa['signal'])
            else:
                self.ax[-1].plot(xx, yy ,'.-', linewidth=1, label=aa['signal'])
                cc=self.ax[-1].get_lines()[-1].get_color()
                self.ax[-1].fill_between(xx, ymin, ymax, facecolor=cc, alpha=0.5)
        self.ax[-1].set_xlabel('time [sec]')
        self.ax[-1].set_ylabel('Allan_dev [int]')
        self.ax[-1].grid(b=True)
        self.ax[-1].legend()
        plt.tight_layout()
    
    def allan_range2(self,signal,start=0,end=1,sp=0,div=16):
        """
        Calculates allan deviation of the signal ( 'signal'- sp ) from 'start' index to 'end' index.
        First, it analyses the data range and auto set the best time bin length to divide the time array.
        The, calculates the mean value of each time bin creating a v_s vector of the signal data that is
        equally spaced in time.
        Then calculates the allan deviation on the v_s vector.
        
        Usage:
            self.allan_range2(signal,start=0,end=1,sp=0,div=16)
        
        Params:
            signal    : signal name to be processed
            start,end : index limits of data to process
            sp        : set-point value to supress from signal
            div       : for time ranges that uses several time bins, the allan deviation is calculated
                        from at most 'div' diferent time offsets. This produces several values for time
                        range, that enables so select the max, min and mean value for error plotting.
            
        
        Example:
            d=read_dump(filename='/home/lolo/data/20171109_184719.bin')
            d.allan_range2(start=6944, end=8148326,signal='ctrl_A')
            d.plot_allan_error()
             
        """
        # First we find the optimal time range
        self.check_time_stats()
        if end==1:
            end=self.time_stats_data['data_length']-1
        print('Analysing vector "{:s}" in range {:d}:{:d}'.format(signal,start,end))
        s_ind=self.names.index(signal)
        max_dt_oom=floor(log10(self.time_stats_data['max_dt']))
        max_dt=ceil(self.time_stats_data['max_dt']*10**(-max_dt_oom))/10**(-max_dt_oom)
        print('Min time bin: {:f} sec'.format(max_dt))
        tbuff=time.time()
        time_already=False
        if len(self.allan)>0:
            for i in self.allan:
                if i['range']==[start,end]:
                    t0=i['t0']
                    t1=i['t1']
                    time_already=True
                    print('already have time info')
                    break
        if not time_already:
            print('Looking for time information')
            with open(self.filename,'rb') as f:
                f.read(self.head_size)
                cs=struct.calcsize(self.strstr)
                fc=f.read(cs)
                j=0
                while fc:
                    tnow=struct.unpack(self.strstr,fc)[0]
                    if j==start:
                        t0=tnow
                    if j==end:
                        t1=tnow
                        break
                    fc=f.read(cs)
                    j+=1
        print('Load time: {:f} sec'.format( time.time()-tbuff ))
        print('t0: {:f} sec'.format( t0 ) )
        print('t1: {:f} sec'.format( t1 ) )
        print('Dt: {:f} sec | {:f} min'.format( t1-t0, (t1-t0)/60 ) )
        print('')
        bins_num=int(  floor(log( (t1-t0)/max_dt )/log(2)) -1 )
        print('Number of bins: {:d}'.format(bins_num))
        
        steps = max_dt * 2**arange(bins_num)
        step  = max_dt
        v_s   = []
        v_n   = []
        v_tmp = []
        v_lasttime = t0
        percentage      = '0%'
        percentage_step = int((end-start)/1000)
        with open(self.filename,'rb') as f:
            f.read(self.head_size)
            cs=struct.calcsize(self.strstr)
            fc=True
            j=0
            for j in range(start):
                fc=f.read(cs)
                j+=1
            while fc:
                fc=f.read(cs)
                vv=struct.unpack(self.strstr,fc)
                tnow=vv[0]
                for i in range(bins_num):
                    if tnow > v_lasttime + step:
                        v_lasttime+=step
                        v_s.append( mean( v_tmp ) )
                        v_n.append(len(v_tmp))
                        v_tmp=[ vv[s_ind] - sp   ]
                        
                    else:
                        v_tmp.append(  vv[s_ind] - sp    )
                j+=1
                if j>end:
                    break
                if int((j-start))%percentage_step==0:
                    if not percentage == str(int((j-start)/(end-start)*100)) + '%':
                        percentage = str(int((j-start)/(end-start)*100)) + '%'
                        print( percentage )
        ss=(steps/steps[0]).astype(int)
        #vv=v_s[:]
        allan_var_all = []
        allan_dev_all = []
        for i in ss:
            print(i)
            alvar=[]
            aldev=[]
            for k in arange(0,i,i/min(i,div)).astype(int):
                np=int(len(v_s[k:])-len(v_s[k:])%i)
                tmp = []
                nnn = []
                for j in range(i):
                    tmp += v_s[k+j:np+k:i]
                    nnn += v_n[k+j:np+k:i]
                tmp = array(tmp).reshape( (i,int(np/i)) )
                nnn = array(nnn).reshape( (i,int(np/i)) )
                #tmp = mean(tmp,axis=1).tolist()
                tmp = sum(tmp*nnn,axis=0)
                nnn = sum(nnn,axis=0)
                tmp = (tmp/nnn).tolist()
                
                if len(v_s[k+np:])>0:
                    tmp.append( sum( array(v_s[k+np:])*array(v_n[k+np:]) ) / sum( array(v_n[k+np:]) ) ) 
                #v_s.append(tmp)
                aa=array(tmp)
                alvar.append( sum((aa[0:-1]-aa[1:])**2) / ( 2 * (len(aa)-1) )  )  
                aldev.append( sqrt(alvar[-1]) )
            allan_var_all.append(alvar)
            allan_dev_all.append(aldev)
        
        allan_dev     = []
        allan_dev_max = []
        allan_dev_min = []
        allan_dev_std = []
        allan_var     = []
        for i in allan_dev_all:
            allan_dev.append(     mean(i) )
            allan_dev_max.append( max(i) )
            allan_dev_min.append( min(i) )
            allan_dev_std.append( std(i) )
        for i in allan_var_all:
            allan_var.append(     mean(i) )
            
        i=len(self.allan)
        self.allan.append( { 'num':i, 'signal':signal, 'signal_index': s_ind,
                             't0':t0  , 't1':t1,
                             'steps':steps, 'v_s':v_s , 'v_n':v_n ,'range': [start,end]  ,
                             'allan_dev_max':allan_dev_max , 'allan_dev_min':allan_dev_min ,
                             #'allan_dev_all':allan_dev_all , 'allan_var_all':allan_var_all ,
                             'allan_dev_std':allan_dev_std, 'factor': 1 ,
                             'allan_var':allan_var , 'allan_dev':allan_dev })
        print('Total Load time: {:f} sec'.format( time.time()-tbuff ))


    
    
    def allan_range(self,signal,start=0,end=1,sp=0):
        """
        Calculates allan deviation of the signal ( 'signal'- sp ) from 'start' index to 'end' index.
        First, it analyses the data range and auto set the best time bin length to divide the time array.
        The, calculates the mean value of each time bin creating a v_s vector of the signal data that is
        equally spaced in time.
        Then calculates the allan deviation on the v_s vector.
        
        Usage:
            self.allan_range(signal,start=0,end=1,sp=0)
        
        Params:
            signal    : signal name to be processed
            start,end : index limits of data to process
            sp        : set-point value to supress from signal            
        
        Example:
            d=read_dump(filename='/home/lolo/data/20171109_184719.bin')
            d.allan_range(start=6944, end=8148326,signal='error')
            d.plot_allan()
             
        """
        # First we find the optimal time range
        self.check_time_stats()
        if end==1:
            end=self.time_stats_data['data_length']-1
        print('Analysing vector "{:s}" in range {:d}:{:d}'.format(signal,start,end))
        s_ind=self.names.index(signal)
        max_dt_oom=floor(log10(self.time_stats_data['max_dt']))
        max_dt=ceil(self.time_stats_data['max_dt']*10**(-max_dt_oom))/10**(-max_dt_oom)
        print('Min time bin: {:f} sec'.format(max_dt))
        tbuff=time.time()
        time_already=False
        if len(self.allan)>0:
            for i in self.allan:
                if i['range']==[start,end]:
                    t0=i['t0']
                    t1=i['t1']
                    time_already=True
                    print('already have time info')
                    break
        if not time_already:
            print('Looking for time information')
            with open(self.filename,'rb') as f:
                f.read(self.head_size)
                cs=struct.calcsize(self.strstr)
                fc=f.read(cs)
                j=0
                while fc:
                    tnow=struct.unpack(self.strstr,fc)[0]
                    if j==start:
                        t0=tnow
                    if j==end:
                        t1=tnow
                        break
                    fc=f.read(cs)
                    j+=1
        print('Load time: {:f} sec'.format( time.time()-tbuff ))
        print('t0: {:f} sec'.format( t0 ) )
        print('t1: {:f} sec'.format( t1 ) )
        print('Dt: {:f} sec | {:f} min'.format( t1-t0, (t1-t0)/60 ) )
        print('')
        bins_num=int(  floor(log( (t1-t0)/max_dt )/log(2)) -1 )
        print('Number of bins: {:d}'.format(bins_num))
        
        steps=max_dt * 2**arange(bins_num)
        v_s=[]
        for i in range(bins_num):
            v_s.append([])
        v_tmp=[]
        for i in range(bins_num):
            v_tmp.append([])
        v_n = []
        for i in range(bins_num):
            v_n.append([])
        v_lastmod  = ones(bins_num)*1e10
        v_lasttime = ones(bins_num)*t0
        percentage      = '0%'
        percentage_step = int((end-start)/1000)
        with open(self.filename,'rb') as f:
            f.read(self.head_size)
            cs=struct.calcsize(self.strstr)
            fc=True
            j=0
            for j in range(start):
                fc=f.read(cs)
                j+=1
            while fc:
                fc=f.read(cs)
                vv=struct.unpack(self.strstr,fc)
                tnow=vv[0]
                for i in range(bins_num):
                    if tnow > v_lasttime[i] + steps[i]:
                        #v_lasttime[i]=tnow
                        v_lasttime[i]+=steps[i]
                        v_s[i].append( mean( v_tmp[i] ) )
                        v_n[i].append(len(v_tmp[i]))
                        v_tmp[i]=[ vv[s_ind] - sp   ]
                    else:
                        v_tmp[i].append(  vv[s_ind] - sp    )
                j+=1
                if j>end:
                    break
                if int((j-start))%percentage_step==0:
                    if not percentage == str(int((j-start)/(end-start)*100)) + '%':
                        percentage = str(int((j-start)/(end-start)*100)) + '%'
                        print( percentage )
        allan_var = []
        for i in v_s:
            aa=array(i)
            allan_var.append(  sum((aa[0:-1]-aa[1:])**2) / ( 2 * (len(aa)-1) )  )
        allan_dev=sqrt(array(allan_var))
        i=len(self.allan)
        self.allan.append( { 'num':i, 'signal':signal, 'signal_index': s_ind,
                             't0':t0  , 't1':t1, 'v_n':v_n ,
                             'steps':steps, 'v_s':v_s , 'range': [start,end]  ,
                             'allan_var':allan_var , 'allan_dev':allan_dev })
        print('Total Load time: {:f} sec'.format( time.time()-tbuff ))


