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

function replaceContents(widgetContents) {
    for (var cssId in widgetContents) {
        var widget = $('#'+cssId);

        widget.find('form').each(function (i, form) {
            $(form).validate().destroy();
        });

        widget.html(widgetContents[cssId]);
    }
}

function reloadPage() {
    $('body').block(blockOptions({cursor: 'wait'}));
    window.location.replace(window.location.href.replace('#', '?'));
//        location.reload(true);
}

function handleStateChanged(refreshUrl, widgetsToRefresh, newState, afterHandler, changedArguments, afterContentsReplacedHandler) {

    newState = addArgumentsToState(newState, getFormInputsAsArguments());
    newState = addArgumentsToState(newState, changedArguments);

    filterQueryStringArgsFromState(newState, refreshUrl);
    history.replaceState(newState, null, null);

    var data = {};
    data['__reahl_client_side_state__'] = $.param(newState, true);

    widgetsToRefresh.block(blockOptions({cursor: 'wait'}));

    $.ajax({url:     refreshUrl,
            method:  'POST',
            data:    data,
            success: function(data, status, xhr){
                if (xhr.getResponseHeader("content-type").startsWith("application/json")) {
                    if (data.exception) {
                        alert(data.exception)
                        reloadPage();
                    } else {
                        replaceContents(data.result);
                        afterContentsReplacedHandler();
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
                widgetsToRefresh.unblock();
                afterHandler();
            },
            traditional: true
    });

}

$.fn.forceReload = function(refreshUrl, widgetsToRefresh, afterHandler) {
    handleStateChanged(refreshUrl, widgetsToRefresh, getCurrentState(), afterHandler, [], function(){});
}

function filterQueryStringArgsFromState(state, refreshUrl){
    var urlQueryString = $.deparam.querystring(refreshUrl);
    for (var i in urlQueryString) {
        if (i in state){
            delete state[i];
        }
    };
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

function calculateChangedArguments(currentState, arguments_) {
    var widgetArguments = $.extend(true, [], arguments_);
    for (var i=0; i<widgetArguments.length; i++) {
        var argument = widgetArguments[i];
        argument.updateFromStateObject(currentState);
    };
    return widgetArguments;
}

function hasChanged(newArguments){
    var changed = false;
    for (var i=0; i<newArguments.length; i++) {
        var argument = newArguments[i];
        if (argument.changed) {
            changed = true;
        };
    }
    return changed;
}

function addArgumentsToState(currentState, widgetArguments) {
    var values = $.extend(true, {}, currentState);
    for (var i=0; i<widgetArguments.length; i++) {
        var argument = widgetArguments[i];
        argument.updateStateObject(values);
    }
    return values;
}

function getFormInputsAsArguments(values){
    return $('.reahl-primitiveinput').map(function(i, v) { 
        var primitiveInput = $(v).data('reahlPrimitiveinput');
        return new WidgetArgument(primitiveInput.getName(), primitiveInput.getCurrentInputValue()); 
    });
}

$.widget('reahl.hashchange', {
    options: {
            url: '',
            params: {}
    },

    _create: function() {
        this.arguments = [];
        var _this = this;

        if (this.navigatedHereViaHistoryButtons()) {
            reloadPage();
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
            var changedArguments = calculateChangedArguments(newState, _this.getArguments());
            if(hasChanged(changedArguments)){
                var afterContentsReplacedHandler = function(){
                    _this.arguments = changedArguments;
                };
        
                handleStateChanged(_this.options.url, _this.element, newState, function(){}, changedArguments, afterContentsReplacedHandler);
            }
        });
        setTimeout(function() { $(window).trigger('hashchange'); }, 0);
    },
    navigatedHereViaHistoryButtons: function() {
        var performanceEntries = performance.getEntriesByType('navigation');
        if (performanceEntries.length == 1) {
            return (performanceEntries[0].type == 'back_forward');
        } else {
            return (performance.navigation.type == 2);
        }
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
        
        completeFragment = addArgumentsToState(partialFragment, this.getArguments());
        fragmentInput.val($.param(completeFragment, true));
    }
});

$.extend($.reahl.hashchange, {
    version: '1.8'
});



})(jQuery);


