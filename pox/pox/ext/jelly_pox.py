from mininet.node import Controller
import os

POXDIR = os.getcwd() + '/../..'

class JELLYPOX( Controller ):
    def __init__( self, name, cdir=POXDIR,
                  command='python pox.py', cargs=('log --file=jelly.log,w openflow.of_01 --port=%s ext.jelly_controller '), cargs2=(''),
                  **kwargs ):
        Controller.__init__( self, name, cdir=cdir,
                             command=command,
                             cargs=cargs+cargs2, **kwargs )
controllers={ 'jelly': JELLYPOX }
