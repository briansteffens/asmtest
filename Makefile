all: ;

install:
	mkdir -p ${DESTDIR}/usr/local/bin
	cp asmtest.py ${DESTDIR}/usr/local/bin/asmtest

symlink:
	mkdir -p ${DESTDIR}/usr/local/bin
	ln -s `pwd`/asmtest.py ${DESTDIR}/usr/local/bin/asmtest

uninstall:
	rm ${DESTDIR}/usr/local/bin/asmtest
