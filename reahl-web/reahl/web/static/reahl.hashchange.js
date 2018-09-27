/* Copyright 2013-2018 Reahl Software Services (Pty) Ltd. All rights reserved. */
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

function getTraditionallyNamedFragment() {
    var untraditionallyNamedFragment = $.deparam.fragment(window.location.hash);
    var traditionallyNamedFragment = {};
    for (var cleanName in untraditionallyNamedFragment) {
        var value = untraditionallyNamedFragment[cleanName];
        var traditionalName;
        if (Array.isArray(value)) {
            traditionalName = cleanName+'[]';
        } else {
            traditionalName = cleanName;
        }
        traditionallyNamedFragment[traditionalName] = value;
    }
    return traditionallyNamedFragment;
}

function HashArgument(name, defaultValue) {
    this.name = name;
    this.value = defaultValue;
    this.changed = false;
    this.changeValue = function(value) {
        if (!_.isEqual(this.value, value)) {
            this.changed = true;
            this.value = value;
        }
    }

    this.getIsList = function() {
        return this.name.match('\\[\\]$');
    }

    this.getIsEmptyList = function() {
        return this.getIsList() && (_.isEqual(this.value, []));
    }

    this.getEmptyListSentinelName = function() {
        return this.name+'-';
    }

    this.updateFromHashObject = function(hashObject) {
        this.changed = false;
        var currentValue = hashObject[this.name];
        if (currentValue) {
            this.changeValue(currentValue);
        } else if (this.getIsList()) {
            if (hashObject[this.getEmptyListSentinelName()] != undefined) {
                this.changeValue([]);
            }
        } 
    }

    this.updateHashObject = function(hashObject) {
        delete hashObject[this.name];
        delete hashObject[this.getEmptyListSentinelName()];

        var nameInHash;
        var valueInHash;
        if (this.getIsEmptyList()) {
            nameInHash = this.getEmptyListSentinelName();
            valueInHash = "";
        } else {
            nameInHash = this.name;
            valueInHash = this.value;
        }

        hashObject[nameInHash] = valueInHash;
    }

}


$.widget('reahl.hashchange', {
    options: {
            url: '',
            cache: true,
            errorMessage: 'Ajax error',
            timeoutMessage: 'Ajax timeout',
            params: [],
            arguments: [],
            registered_callbacks: {}
    },

    _create: function() {
        var o = this.options;
        var element = this.element;
        var _this = this;

        _this.options.previousHashValues = $.extend(true, {}, _this.options.params);
        _this.options.arguments = [];
        for (name in _this.options.params) {
            _this.options.arguments.push(new HashArgument(name, _this.options.params[name]))
        }
        $(window).on( 'hashchange', function(e) {
            var currentFragment = getTraditionallyNamedFragment();
            var changedArguments = _this.calculateChangedArguments(currentFragment);
            if (_this.hasChanged(changedArguments)) {
                _this.triggerChange(currentFragment, changedArguments);
            };
            return true;
        });

        $(window).trigger( 'hashchange' );
    },
    getArguments: function() {
        return this.options.arguments;
    },
    addCallback: function(name, callback) {
        this.options.registered_callbacks[name] = callback;
    },
    popCallback: function() {
        var currentFragment = getTraditionallyNamedFragment();
        var name = currentFragment['__and_then__'];
        if (name !== undefined) {
            delete currentFragment['__and_then__'];
        }
        window.location.hash = $.param(currentFragment, true);

        var callback = this.options.registered_callbacks[name];        
        if (callback !== undefined) {
            delete this.options.registered_callbacks[name];
            return callback;
        } else {
            return function(){}
        }
    },
    calculateQueryStringValues(currentHashValues, hashArguments) {
        var values = $.extend(true, {}, currentHashValues);
        for (var i=0; i<hashArguments.length; i++) {
            var argument = hashArguments[i];
            argument.updateHashObject(values);
        }
        return values;
    },
    triggerChange: function(currentHashValues, newArguments) {
        var _this = this;

        var after_handler = _this.popCallback();

        _this.element.block({overlayCSS: {backgroundColor: '#fff', opacity: 0.3}, message: '', fadeIn: 0, fadeout: 0});
        $.ajax({url:     _this.options.url,
                cache:   _this.options.cache,
                data:    _this.calculateQueryStringValues(currentHashValues, newArguments),
                success: function(data){
                    _this.element.html(data);
                    _this.options.arguments = newArguments;
                },
                complete: function(data){
                    _this.element.unblock();
                    after_handler();
                },
                traditional: true
        });
    },
    hasChanged: function(newArguments){
        var _this = this;
        var changed = false;
        for (var i=0; i<newArguments.length; i++) {
            var argument = newArguments[i];
            if (argument.changed) {
                changed = true;
            };
        }
        return changed;
    },
    calculateChangedArguments: function(currentHashValues) {
        var _this = this;
        var hashArguments = $.extend(true, [], _this.getArguments());
        for (var i=0; i<hashArguments.length; i++) {
            var argument = hashArguments[i];
            argument.updateFromHashObject(currentHashValues);
        };
        return hashArguments;
    },
});

$.extend($.reahl.hashchange, {
    version: '1.8'
});


$.widget('reahl.changenotifier', {
    options: {
        name: undefined,
        widget_id: undefined,
        is_boolean: false,
        true_boolean_value: undefined,
        false_boolean_value: undefined,
        argument: undefined
    },
    _create: function() {
            var o = this.options;
            var element = this.element;
            var _this = this;

            if (!o.name) { throw new Error("No name given in options. This is a required option.")}

            $(element).attr('data-target-widget', o.widget_id);
            $(element).on( 'change', function(e) {
                if (_this.getIsSelfValid()) {
                    _this.updateCurrentValue(e.target);
                }
                if (_this.getIsValid()) {
                    var currentFragment = getTraditionallyNamedFragment();
                    _this.blockAllSiblingInputs(currentFragment);
                    _this.updateHashWithAllSiblingValues(currentFragment);
                    this.focus();
                    _this.unblockWidget();
                } else { _this.blockWidget(); }
                return true;
            });
    },

    isCheckbox: function(input) {
        return $(input).attr('type') === 'checkbox';
    },

    isForBooleanValue: function(checkbox) {
        return this.options.is_boolean;
    },

    getCheckboxListValue: function(checkbox) {
        var checkedCheckboxes = $('input[name="' + $(checkbox).attr("name") + '"][form="' + $(checkbox).attr("form") + '"]:checked');
        return checkedCheckboxes.map(function() {
            return $(this).val();
        }).toArray();
    },

    getCheckboxBooleanValue: function(checkbox) {
       var _this = this;
       if($(checkbox).is(":checked"))
            return _this.options.true_boolean_value;
       else
            return _this.options.false_boolean_value;
    },

    getCurrentInputValue: function(currentInput) {
        if (this.isCheckbox(currentInput)) {
            if (this.isForBooleanValue(currentInput)){
                return this.getCheckboxBooleanValue(currentInput)
            } else {
                return this.getCheckboxListValue(currentInput);
            }
        } else {
            return $(currentInput).val();
        }
    },
    updateCurrentValue: function(currentInput) {
        var _this = this;
        var currentInputValue = this.getCurrentInputValue(currentInput);
        if (_this.options.argument == undefined) {
            _this.options.argument = new HashArgument(this.options.name, currentInputValue);
        }
        var argument = _this.options.argument;
        argument.changeValue(currentInputValue);
    },
    blockAllSiblingInputs: function(currentFragment) {
        var _this = this;
        var uniqueId = new Date().getTime();
        uniqueId += (parseInt(Math.random() * 100)).toString();
        uniqueId = 'cb-' + uniqueId;

        var form = this.getForm();
        form.block({overlayCSS: {backgroundColor: '#fff', opacity: 0.3}, message: '', fadeIn: 0, fadeout: 0});
        this.addAfterHandler(uniqueId, function() { form.unblock(); } );
        currentFragment['__and_then__'] = uniqueId;
    },
    updateHashWithAllSiblingValues: function(currentFragment) {
        this.getSiblingChangeNotifiers().each(function() {
            this.addCurrentInputValueTo(currentFragment);
            
        });
        var newHash = $.param(currentFragment, true);
        window.location.hash = newHash;
    },
    addCurrentInputValueTo: function(fragment) {
        var argument = this.options.argument;
        if (argument !== undefined) {
            argument.updateHashObject(fragment);
        }
    },
    getInputs: function() {
        if (this.element[0].form !== undefined) {
            return this.element;
        } else {
            return this.element.find('input');
        }
    },
    getForm: function() {
        return $(this.getInputs()[0].form);
    },
    getIsSelfValid: function() {
        var validator = this.getForm().data('validator');
        return validator.element(this.getInputs());
    },
    addAfterHandler: function(name, handler) {
        $('#'+this.options.widget_id).data('reahlHashchange').addCallback(name, handler);
    },
    getSiblings: function() {
        return $('[data-target-widget="' + this.options.widget_id + '"]');
    },
    getSiblingChangeNotifiers: function() {
        return this.getSiblings().map(function() {
            return $(this).data('reahlChangenotifier')
        });
    },
    getIsSiblingArgumentsValid: function() {
        var _this = this;
        var valid = true;
        this.getSiblingChangeNotifiers().each(function() {
            var sibling = this;
            if (sibling !== _this) {
                valid = valid && sibling.getIsSelfValid();
            }
        });
        return valid;
    },
    getIsValid: function() {
        return this.getIsSelfValid() && this.getIsSiblingArgumentsValid();
    },
    blockWidget: function() {
        $('#'+this.options.widget_id).block({overlayCSS: {backgroundColor: '#fff', opacity: 0.3}, message: '', fadeIn: 0, fadeout: 0});
    },
    unblockWidget: function() {
        $('#'+this.options.widget_id).unblock();
    }
});

$.extend($.reahl.changenotifier, {
version: '1.0'
});


})(jQuery);


