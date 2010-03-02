# -*- coding: utf-8 -*-
# Created By: Virgil Dupras
# Created On: 2010-02-28
# Copyright 2010 Hardcoded Software (http://www.hardcoded.net)
# 
# This software is licensed under the "HS" License as described in the "LICENSE" file, 
# which should be included with this package. The terms are also available at 
# http://www.hardcoded.net/licenses/hs_license

from nose.tools import eq_

from ..base import TestApp, with_app

#--- Default completable edit
def app_default():
    app = TestApp()
    app.add_txn(description='Bazooka')
    app.add_txn(description='buz')
    app.add_txn(description='bar')
    app.add_txn(description='foo')
    app.ce = app.completable_edit(app.ttable, 'description')
    return app

@with_app(app_default)
def test_set_text_matching(app):
    # When text is set with text that matches something in the source, the text is completed.
    app.ce.text = 'f'
    eq_(app.ce.completion, 'oo')

@with_app(app_default)
def test_set_text_not_matching(app):
    # When the text doesn't match, there's no completion
    app.ce.text = 'z'
    eq_(app.ce.completion, '')

@with_app(app_default)
def test_commit_partial(app):
    # Commit takes the current completion and sets the text with it, overriding previous upper or
    # lowercase in existing text. That is, however, only if the text is partial to the completion.
    app.ce.text = 'baz'
    app.ce.commit()
    eq_(app.ce.text, 'Bazooka')
    eq_(app.ce.completion, '')

@with_app(app_default)
def test_commit_complete(app):
    # When the user completly types a string, we keep his case intact.
    app.ce.text = 'Buz'
    app.ce.commit()
    eq_(app.ce.text, 'Buz')
    eq_(app.ce.completion, '')

#--- Edit with match
def app_with_match():
    app = TestApp()
    app.add_txn(description='Bazooka')
    app.add_txn(description='buz')
    app.add_txn(description='bar')
    app.add_txn(description='foo')
    app.ce = app.completable_edit(app.ttable, 'description')
    app.ce.text = 'b'
    return app

@with_app(app_with_match)
def test_add_text_without_match(app):
    # Settings the text to something that doesn't match makes the completion empty.
    app.ce.text = 'bz'
    eq_(app.ce.completion, '')

@with_app(app_with_match)
def test_up(app):
    # up() makes the completion go up in the list
    app.ce.up()
    eq_(app.ce.completion, 'azooka')

@with_app(app_with_match)
def test_down(app):
    # down() makes the completion go down in the list
    app.ce.down()
    eq_(app.ce.completion, 'uz')

@with_app(app_with_match)
def test_set_source(app):
    # Setting the source resets text and completion
    app.ce.source = app.ce.source
    app.ce.commit()
    eq_(app.ce.text, '')
    eq_(app.ce.completion, '')

@with_app(app_with_match)
def test_set_attrname(app):
    # Setting the attrname resets text and completion
    app.ce.attrname = 'foo'
    app.ce.commit()
    eq_(app.ce.text, '')
    eq_(app.ce.completion, '')