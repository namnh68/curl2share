#!/usr/bin/env python
# -*- coding: utf-8 -*-

from upload.handlers import app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
