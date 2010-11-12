
BINDIR = /usr/local/bin

INSTALL = install

all:

install:
	$(INSTALL) -m 755 aggr.py $(BINDIR)/aggr

uninstall:
	rm $(BINDIR)/aggr
