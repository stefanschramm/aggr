
PREFIX = /usr
BINDIR = $(PREFIX)/bin
MANDIR = $(PREFIX)/share/man/man1

INSTALL = install

all:	README

install:
	$(INSTALL) -m 755 aggr.py $(BINDIR)/aggr
	$(INSTALL) -m 644 doc/aggr.1 $(MANDIR)/aggr.1

uninstall:
	rm $(BINDIR)/aggr
	rm $(MANDIR)/aggr.1

README:	doc/aggr.1
	# readme is the manpage
	MANWIDTH="76" man -P cat -l doc/aggr.1 > README

