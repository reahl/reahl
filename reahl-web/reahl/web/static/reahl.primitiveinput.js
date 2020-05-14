/* Copyright 2019 Reahl Software Services (Pty) Ltd. All rights reserved. */
/*
    This file is part of Reahl.

    Reahl is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation; version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/


(function($) {
    "use strict";
    
    $.widget("reahl.primitiveinput", {
        options: {
        },

        _create: function() {
            var o = this.options;
            var _this = this;
            this.busyTabbing = false;
            this.shift = false;
            this.focussedElement = undefined;
            this.buffer = [];
            this.element.addClass("reahl-primitiveinput");
    
            this.getAllRelatedFormInputs().data('reahlPrimitiveinput', this);

            if (this.getRefreshWidgetId()) {
                this.element.on('keydown', function(e) {
                    if ( e.which == 9 ) {
                        _this.busyTabbing = true;
                        _this.shift = e.shiftKey;
                        _this.focussedElement = $(':focus');
                        e.preventDefault();
                        setTimeout(function() {_this.element.change() }, 0);
                    } 
                });

                this.element.on('keypress', function(e) {
                    if ( _this.busyTabbing ) {
                        _this.buffer.push(e.which);
                        e.preventDefault();
                    }
                });

                this.element.on('change', function(e) {
                    if (_this.isValid()) { 
                        $('#'+_this.getRefreshWidgetId()).data('reahlHashchange').forceReload(function(){ 
                            var newFocussedElement;
                            if (_this.busyTabbing) {
                                var currentInput = _this.focussedElement;
                                var inputId = currentInput.attr('id');
                                var selectorForFocus = '#'+inputId;

                                var focusables = $(":tabbable");//focusable
                                var current = focusables.index($(selectorForFocus));
                                var next;
                                if (_this.shift) {
                                    next = current-1 < 0 ? focusables.length-1 : current-1;
                                } else {
                                   next = current+1 > focusables.length-1 ? 0 : current+1;
                                }
                                newFocussedElement = focusables.eq(next);
                            } else {
                                var currentInput = $(e.target);
                                var inputId = currentInput.attr('id');
                                newFocussedElement = $( '#'+inputId);
                            }

                            _this.busyTabbing = false;
                            _this.shift = false;
                            newFocussedElement.focus();
                        });
                    } else {
                        _this.busyTabbing = false;
                        _this.shift = false;
                    }
                })
            };
        },

        getForm: function() {
            var inputs = this.getAllRelatedFormInputs();
            if (inputs.length < 1) { throw new Error('Expected at least one form input'); };
            return $(inputs[0].form);
        },

        isValid: function() {
            return this.getForm().validate().element(this.getAllRelatedFormInputs());
        },
        
        isCheckbox: function() {
            return this.getAllRelatedFormInputs().is('input[type="checkbox"]');
        },
    
        isRadio: function() {
            return this.getAllRelatedFormInputs().is('input[type="radio"]');
        },

        getRefreshWidgetId: function() {
            return this.element.attr('data-refresh-widget-id');
        },
                    
        isForBooleanValue: function() {
            return this.element.attr('data-is-boolean') !== undefined;
        },
    
        getBooleanTrueValue: function() {
            return this.element.attr('data-true-boolean-value');
        },

        getBooleanFalseValue: function() {
            return this.element.attr('data-false-boolean-value');
        },

        getCheckboxListValue: function() {
            var checkedCheckboxes = this.getAllRelatedFormInputs().filter('input:checked');
            return checkedCheckboxes.map(function() {
                return $(this).val();
            }).toArray();
        },
    
        getCheckboxBooleanValue: function() {
            var checkbox = this.getAllRelatedFormInputs().filter('input[type="checkbox"]');
            if (checkbox.length != 1) { throw new Error('Expected an input type checkbox'); };

            if(checkbox.is(":checked"))
                return this.getBooleanTrueValue();
            else
                return this.getBooleanFalseValue();
        },
    
        getRadioValue: function() {
            var checkedRadio = this.getAllRelatedFormInputs().filter(':checked');
            if (checkedRadio.length == 1) {
                return checkedRadio.val();
            } else {
                return '';
            }
        },

        getAllRelatedFormInputs: function() {            
            if (this.element.prop('form') !== undefined)  {
                return this.element;
            } else {
                return this.element.find('[form]');
            }
        },

        getFormInput: function() {            
            var input = this.getAllRelatedFormInputs();
            if (input.length != 1) { throw new Error('Expected one and only one form input'); };
            return input;
        },

        getName: function() {
            return this.getAllRelatedFormInputs().attr('name');
        },

        getCurrentInputValue: function() {
            if (this.isCheckbox()) {
                if (this.isForBooleanValue()){
                    return this.getCheckboxBooleanValue()
                } else {
                    return this.getCheckboxListValue();
                }
            } else if (this.isRadio()) {
                return this.getRadioValue();
            } else {
                return this.getFormInput().val();
            }
        }
    

    });
    
    $.extend($.reahl.primitiveinput, {
        version: "1.8"
    });
    
    })(jQuery);
    
    
    
