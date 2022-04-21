/* Copyright 2013-2022 Reahl Software Services (Pty) Ltd. All rights reserved. */
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

function blockOptions(extraCSS) {
    var defaultOverlayCSS =  { backgroundColor: '#fff', opacity: 0.3 };
    return {overlayCSS: $.extend(defaultOverlayCSS, extraCSS), message: '', fadeIn: 0, fadeout: 0};
}

function getTraditionallyNamedFragment() {
    return mapToTraditionalNames($.deparam.fragment(window.location.hash));
}

function getCurrentState() {
    var savedState = {};
    if (history.state !== undefined) {
        savedState = history.state;
    }
    return savedState;
}

function mapToTraditionalNames(untraditionallyNamedArguments) {
    var traditionallyNamedArguments = {};
    for (var cleanName in untraditionallyNamedArguments) {
        var value = untraditionallyNamedArguments[cleanName];
        var traditionalName;
        if (Array.isArray(value)) {
            traditionalName = cleanName+'[]';
        } else {
            traditionalName = cleanName;
        }
        traditionallyNamedArguments[traditionalName] = value;
    }
    return traditionallyNamedArguments;
}

function WidgetArgument(name, defaultValue) {
    this.name = name;
    this.value = defaultValue;
    this.changed = false;
    this.changeValue = function(value) {
        if (!underscore.isEqual(this.value, value)) {
            this.changed = true;
            this.value = value;
        }
    }

    this.getIsList = function() {
        return this.name.match('\\[\\]$');
    }

    this.getIsEmptyList = function() {
        return this.getIsList() && (underscore.isEqual(this.value, []));
    }

    this.getEmptyListSentinelName = function() {
        return this.name+'-';
    }

    this.updateFromStateObject = function(stateObject) {
        this.changed = false;
        var currentValue = stateObject[this.name];
        if (currentValue) {
            this.changeValue(currentValue);
        } else if (this.getIsList()) {
            if (stateObject[this.getEmptyListSentinelName()] != undefined) {
                this.changeValue([]);
            }
        } 
    }

    this.updateStateObject = function(stateObject) {
        delete stateObject[this.name];
        delete stateObject[this.getEmptyListSentinelName()];
        
        var nameInHash;
        var valueInHash;
        if (this.getIsEmptyList()) {
            nameInHash = this.getEmptyListSentinelName();
            valueInHash = '';
        } else {
            nameInHash = this.name;
            valueInHash = this.value;
        }

        stateObject[nameInHash] = valueInHash;
    }

    this.clearFromStateObject = function(stateObject) {
        this.deleteFromStateObject(stateObject);
    }
        
    this.deleteFromStateObject = function(stateObject) {
        delete stateObject[this.name];
        delete stateObject[this.getEmptyListSentinelName()];
    }
}


$.widget('reahl.hashchange', {
    options: {
            url: '',
            cache: true,
            errorMessage: 'Ajax error',
            timeoutMessage: 'Ajax timeout',
            params: []
    },

    _create: function() {
        this.arguments = [];
        var _this = this;

        if (this.navigatedHereViaHistoryButtons()) {
            _this.reloadPage();
        }
        
        for (name in _this.options.params) {
            _this.arguments.push(new WidgetArgument(name, _this.options.params[name]))
        }

        $('html').filter('[data-reahl-rendered-state]').each(function() {
            var renderedState = $('html').attr('data-reahl-rendered-state');
            $('html').removeAttr('data-reahl-rendered-state');
            history.replaceState($.deparam.fragment(renderedState), null, null);
        });
        
        
        var namespaced_submit = 'submit.'+this.element.attr('id');
        this.element.parents('form').off(namespaced_submit).on(namespaced_submit, function(e) {
            var form = $(this);
            _this.updateFormActionWithCurrentState(form);
        });

        var namespaced_hashchange = 'hashchange.'+this.element.attr('id');
        $(window).off(namespaced_hashchange).on(namespaced_hashchange, function(e) {
            var newState = $.extend(true, getCurrentState(), getTraditionallyNamedFragment());
            _this.handleStateChanged(newState, function(){}, false);
        });
        setTimeout(function() { $(window).trigger('hashchange'); }, 0);
    },
    forceReload: function(afterHandler) { 
        this.handleStateChanged(getCurrentState(), afterHandler, true);
    },
    handleStateChanged: function(newState, afterHandler, forceChanged) {
        var relevantFormInputs = this.getFormInputsAsArguments({});
        newState = this.addArgumentsToState(newState, relevantFormInputs);
        history.replaceState(newState, null, null);
        var changedArguments = this.calculateChangedArguments(newState);
        if (forceChanged || this.hasChanged(changedArguments)) {
            this.triggerChange(newState, changedArguments, afterHandler);
        };
    },
    navigatedHereViaHistoryButtons: function() {
        var performanceEntries = performance.getEntriesByType('navigation');
        if (performanceEntries.length == 1) {
            return (performanceEntries[0].type == 'back_forward');
        } else {
            return (performance.navigation.type == 2);
        }
    },
    reloadPage: function() {
        $('body').block(blockOptions({cursor: 'wait'}));
        location.reload(true);
    },
    getArguments: function() {
        return this.arguments;
    },
    updateFormActionWithCurrentState(form) {
        var fragmentInput = $('input[form="'+ form.attr('id')+'"][name="__reahl_client_side_state__"]');
        var completeFragment;
        var partialFragment;
        if (fragmentInput.length == 0) {
            fragmentInput = $('<input name="__reahl_client_side_state__" form="' + form.attr('id') + '" type="hidden">');
            fragmentInput.appendTo(form);
            partialFragment = getCurrentState();
        } else {
            var handledFragmentPart = $.deparam.querystring(fragmentInput.val());
            partialFragment = $.extend(true, getCurrentState(), handledFragmentPart);
        }
        
        completeFragment = this.addArgumentsToState(partialFragment, this.getArguments());
        fragmentInput.val($.param(completeFragment, true));
    },
    addArgumentsToState(currentState, widgetArguments) {
        var values = $.extend(true, {}, currentState);
        for (var i=0; i<widgetArguments.length; i++) {
            var argument = widgetArguments[i];
            argument.updateStateObject(values);
        }
        return values;
    },
    calculatePOSTFragment(currentState, widgetArguments) {
        var values = this.addArgumentsToState(currentState, widgetArguments);
        var urlQueryString = $.deparam.querystring(this.options.url);
        for (var i in urlQueryString) {
            if (i in values){
                delete values[i];
            }
        };
        
        return values;
    },
    getFormInputsAsArguments: function(values){
        return $('.reahl-primitiveinput').map(function(i, v) { 
            var primitiveInput = $(v).data('reahlPrimitiveinput');
            return new WidgetArgument(primitiveInput.getName(), primitiveInput.getCurrentInputValue()); 
        }).filter(function(i,v){ return ! (v.name in values) });
    },
    triggerChange: function(newState, newArguments, afterHandler) {
        var _this = this;

        var data = {};
        data['__reahl_client_side_state__'] = $.param(_this.calculatePOSTFragment(newState, newArguments), true);  

        _this.element.block(blockOptions({cursor: 'wait'}));
        $.ajax({url:     this.options.url,
                method:  'POST',
                cache:   _this.options.cache,
                data:    data,
                success: function(data, status, xhr){
                    if (xhr.getResponseHeader("content-type").startsWith("application/json")) {
                        if (data.exception) {
                            alert(data.exception)
                            window.location.replace(window.location.href);
                        } else {
                            _this.element.find('form').each(function (i, form) {
                                $(form).validate().destroy();
                            });
                            _this.replaceContents(data.result);
                            _this.arguments = newArguments;
                        }
                    } else {
                        document.open();
                        document.write(data);
                        document.close();
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    var errorUrl = window.location.origin+"/error?error_message="+encodeURIComponent(errorThrown)+"&error_source_href="+encodeURIComponent(window.location.href);
                    window.location.href = errorUrl;
                },
                complete: function(data){
                    _this.element.unblock();
                    afterHandler();
                },
                traditional: true
        });
    },
    replaceContents: function(widgetContents) {
        for (var cssId in widgetContents) {
            var widget = $('#'+cssId);
            widget.html(widgetContents[cssId]);
        }
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
    calculateChangedArguments: function(currentState) {
        var _this = this;
        var widgetArguments = $.extend(true, [], _this.getArguments());
        for (var i=0; i<widgetArguments.length; i++) {
            var argument = widgetArguments[i];
            argument.updateFromStateObject(currentState);
        };
        return widgetArguments;
    },
});

$.extend($.reahl.hashchange, {
    version: '1.8'
});



})(jQuery);


