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
            arguments: []
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
                    console.log("DONE...ajaxed 3");
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
        is_boolean: false,
        true_boolean_value: undefined,
        false_boolean_value: undefined,
    },
    _create: function() {
            var o = this.options;
            var element = this.element;
            var _this = this;

            if (!o.name) { throw new Error("No name given in options. This is a required option.")}

            $(element).on( 'change', function(e) {
                _this.updateHashWithCurrentInputValue(e.target);
                $(window).hashchange();
                this.focus();
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
        var checkboxValues = [];
        var checkedCheckboxes = $('input[name="' + $(checkbox).attr("name") + '"][form="' + $(checkbox).attr("form") + '"]:checked');
        checkedCheckboxes.map(function() {
            var checkbox = this;
            checkboxValues.push($(checkbox).val());
        });
        return checkboxValues;
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
    updateHashWithCurrentInputValue: function(currentInput) {

        var _this = this;
        var currentFragment = getTraditionallyNamedFragment();
        var currentInputValue = this.getCurrentInputValue(currentInput);
        var argument = new HashArgument(this.options.name, currentInputValue);

        argument.updateHashObject(currentFragment);

        var newHash = $.param(currentFragment, true);
        window.location.hash = newHash;
    }
});

$.extend($.reahl.changenotifier, {
version: '1.0'
});


})(jQuery);


