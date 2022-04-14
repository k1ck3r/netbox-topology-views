const gulp = require('gulp')
const concat = require('gulp-concat')
const terser = require('gulp-terser')
const cleanCss = require('gulp-clean-css')

const jsVendorFiles = [
    'node_modules/vis-network/standalone/umd/vis-network.min.js'
]

const cssVendorFiles = [
    'node_modules/vis-network/dist/dist/vis-network.min.css'
]
const cssFiles = './netbox_topology_views/static_dev/css/*.css',
    cssDest = './netbox_topology_views/static/netbox_topology_views/css/'

const jsLocalResourceFiles = './netbox_topology_views/static_dev/js/*.js',
    jsDest = './netbox_topology_views/static/netbox_topology_views/js/'

function styles_local() {
    return gulp
        .src(cssFiles)
        .pipe(concat('app.css'))
        .pipe(cleanCss())
        .pipe(gulp.dest(cssDest))
}
exports.styles_local = styles_local

function styles_vendor() {
    return gulp
        .src(cssVendorFiles)
        .pipe(concat('vendor.css'))
        .pipe(cleanCss())
        .pipe(gulp.dest(cssDest))
}
exports.styles_vendor = styles_vendor

function js_local() {
    return gulp
        .src(jsLocalResourceFiles)
        .pipe(concat('app.js'))
        .pipe(terser())
        .pipe(gulp.dest(jsDest))
}
exports.js_local = js_local

function js_vendor() {
    return gulp
        .src(jsVendorFiles)
        .pipe(concat('vendor.js'))
        .pipe(terser())
        .pipe(gulp.dest(jsDest))
}
exports.js_vendor = js_vendor

function js_local_dev() {
    return gulp
        .src(jsLocalResourceFiles)
        .pipe(concat('app.js'))
        .pipe(gulp.dest(jsDest))
}
exports.js_local_dev = js_local_dev

function js_vendor_dev() {
    return gulp
        .src(jsVendorFiles)
        .pipe(concat('vendor.js'))
        .pipe(gulp.dest(jsDest))
}
exports.js_vendor_dev = js_vendor_dev

exports.css = gulp.series(styles_local, styles_vendor)

exports.js = gulp.series(js_local, js_vendor)
exports.js_dev = gulp.series(js_local_dev, js_vendor_dev)

exports.build = gulp.series(exports.css, exports.js)
exports.build_dev = gulp.series(exports.css, exports.js_dev)
