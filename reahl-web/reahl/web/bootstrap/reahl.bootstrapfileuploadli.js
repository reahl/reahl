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

function renderButton(name, label, form_id) {
    return '<input class="btn btn-outline-secondary" type="submit" name="'+name+'" value="'+label+'" form="'+form_id+'">';
}

$.widget('reahl.bootstrapfileuploadli', {
    options: {
        file: undefined,
        fileInputPanel: undefined
    },

    getRemoveLabel: function() {
        return this.getFileInputPanel().getRemoveLabel();
    },

    getCancelLabel: function() {
        return this.getFileInputPanel().getCancelLabel();
    },

    getErrorMessage: function() {
        return this.getFileInputPanel().getErrorMessage();
    },
    getFileInputPanel: function() {
        return this.options.fileInputPanel || $(this.element).closest('.reahl-bootstrap-file-upload-panel').data('reahl-bootstrapfileuploadpanel');
    },

    getFormId: function() {
        return this.getFileInputPanel().getFormId();
    },

    getNestedFormId: function() {
        return this.getFileInputPanel().getNestedFormId();
    },

    getFilename: function() {
        // See http://blog.new-bamboo.co.uk/2010/7/30/html5-powered-ajax-file-uploads - Firefox comments.
        return this.options.file.name || this.options.file.fileName;
    },

    getAjaxOptions: function() {
        return this.getFileInputPanel().options;
    },

    _create: function() {
	this.jqXhr = undefined;
        $(this.element).addClass('reahl-bootstrap-file-upload-li');
        if ( !$(this.element).children().length ) {
            this.state = 'file chosen';
        } else {
            this.state = 'uploaded';
        }
    },
    createRemoveButton: function() {
        var removeName = this.getFileInputPanel().getRemoveFileButtonName()+'?filename='+encodeURIComponent(this.getFilename());
        return $(renderButton(removeName, this.getRemoveLabel(), this.getFormId()));
    },
    getRemoveButton: function() {
        return $(this.element).find('input[name^="'+this.getFileInputPanel().getRemoveFileButtonName()+'"]' );
    },
    createFileNameSpan: function() {
        return $('<span>'+this.getFilename()+'</span>');
    },
    getFileNameSpan: function() {
        return $(this.element).find('span');
    },
    createProgressBar: function() {
        return $('<progress class="progress" max=100>0%</progress>');
    },
    getProgressBar: function() {
        return $(this.element).find('progress');
    },
    createCancelButton: function() {
        var cancelName = 'cancel?filename='+encodeURIComponent(this.getFilename());
        return $(renderButton(cancelName, this.getCancelLabel(), this.getFormId()));
    },
    getCancelButton: function() {
        return $(this.element).find('input[name^="cancel"]');
    },
    removeUploaded: function(ajaxOptions) {
        var this_ = this;
        this_.getFileInputPanel().clearFileInput();
        var data = {'_noredirect':''};
        data[this_.getRemoveButton().attr('name')] = '';
        $('#'+this.getFormId()).ajaxSubmit({
            data:  data,
            cache: false,
            beforeSubmit: function(a, form, options) {
            },
            success: function(data){
                if (data.success) {
                    var fileInput = this_.getFileInputPanel().getFileInput(); /* has to be found before element is removed */
                    this_.element.remove();
                    fileInput.trigger('focusout').trigger('focus'); /* to revalidate the input after removal */
                } else {
                    this_.replaceContents(data.result);
                }
            },
            error: function(jqXHR, textStatus, errorThrown){
                this_.changeToFailed(this_.getErrorMessage());
            }
        });
    },
    replaceContents: function(widgetContents) {
        for (var cssId in widgetContents) {
            var html = widgetContents[cssId];
            var widget = $('#'+cssId);
            widget.empty();
            widget.append(html);
        }
    },
    cancelUpload: function() {
	var this_ = this;
        if (this_.jqXhr) {
            this_.jqXhr.abort();
	    this_.jqXhr = undefined;
	    this_.getFileInputPanel().cancelCurrentlyUploading();
        } else {
	    this_.getFileInputPanel().cancelQueuedUpload(this_.getFilename())
        }
        $(this_.element).remove();
    },
    startUpload: function(submitName, ajaxOptions) {
        var this_ = this;
        $(this.element).append(this.createCancelButton().on('click', function(){
            this_.cancelUpload();
        }));
        $(this.element).append(this.createFileNameSpan());
        $(this.element).append(this.createProgressBar());
        var startThisUpload = function() {
            var data = {'_noredirect':''};
            data[submitName] = '';

            this_.state = 'upload started';
            $('#'+this_.getFormId()).ajaxSubmit({
                data: data,
                cache: false,
                beforeSubmit: function(a, form, options) {
                    this_.changeFileInputToSingle(a, this_.options.file);
                },
                beforeSend: function(jqXHR, settings) {
                    this_.saveJqXhr(jqXHR);
                },
                success: function(data){
                    if (data.success) {
                        this_.changeToUploaded();
                    } else {
                        this_.replaceContents(data.result);
                    }
                    this_.getFileInputPanel().uploadFinished();
                },
                error: function(jqXHR, textStatus, errorThrown){
                    this_.getFileInputPanel().uploadFinished();
                    this_.changeToFailed(this_.getErrorMessage());
                },
                uploadProgress: function(event, position, total, percentComplete){
                    this_.updateProgress(percentComplete);
                }
            });
        };
        this_.getFileInputPanel().uploadStarted(this_.getFilename(), startThisUpload);
    },
    saveJqXhr: function(jqXhr) {
	this.jqXhr = jqXhr
    },
    changeFileInputToSingle: function(array, file) {
        var inputName = this.getFileInputPanel().getFileInput().attr('name');
        var cleaned = array.filter(element => element.name != inputName);
        cleaned.push({name:inputName, value:file});
        array.splice(0);
        array.push.apply(array, cleaned);
    },
    changeToUploaded: function(){
        this.getProgressBar().replaceWith('');
        this.getCancelButton().replaceWith(this.createRemoveButton());
        this.state = 'uploaded';
    },
    changeToFailed: function(errorMessage){
        var errorLabel = $('<span class="invalid-feedback">'+errorMessage+'</span>');
        var formGroup = $(this.element).closest('.form-group');
        var formControl = $(this.element).closest('.form-control');

        formControl.addClass('is-invalid');
        if (this.state === 'uploaded' ) {
            formGroup.append(errorLabel);
            this.getRemoveButton().prop('disabled', true);
        } else {
            this.getProgressBar().replaceWith(errorLabel);
            this.getCancelButton().prop('disabled', true);
        }
        this.state = 'failed';
    },
    updateProgress: function(percentComplete){
        this.getProgressBar().attr('value', percentComplete);
        this.getProgressBar().html(percentComplete+'%');
    },

});

$.extend($.reahl.bootstrapfileuploadli, {
    version: '1.8'
});

})(jQuery);




