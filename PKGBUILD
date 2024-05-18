# Maintainer: Tobias Jennerjahn <tobias@jennerjahn.xyz>

pkgname=eyesight
pkgver=0.1
pkgrel=1
pkgdesc="A PyQt5 systray application to remind you to take breaks."
arch=('any')
url="https://github.com/tjennerjahn/eyesight"
license=('MIT')
depends=('python' 'python-pyqt5')
source=("https://github.com/tjennerjahn/eyesight/archive/v$pkgver.tar.gz")
sha256sums=('SKIP')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python setup.py install --root="$pkgdir/" --optimize=1
    install -Dm644 eyesight.desktop "$pkgdir/usr/share/applications/eyesight.desktop"
    install -Dm644 eyesight/icon.png "$pkgdir/usr/share/pixmaps/eyesight.png"
}
