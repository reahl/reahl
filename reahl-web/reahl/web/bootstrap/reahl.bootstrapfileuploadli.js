/* Copyright 2016 Reahl Software Services (Pty) Ltd. All rights reserved. */
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
    return '<input class="btn" type="submit" name="'+name+'" value="'+label+'" form="'+form_id+'">';
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
        var removeName = 'event.remove_file?filename='+encodeURIComponent(this.getFilename());
        return $(renderButton(removeName, this.getRemoveLabel(), this.getFormId()));
    },
    getRemoveButton: function() {
        return $(this.element).find('input[name^="event.remove_file"]');
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
                    fileInput.focusout().focus(); /* to revalidate the input after removal */
                } else {
                    this_.replaceNestedFormContents(data.widget);
                }
            },
            error: function(jqXHR, textStatus, errorThrown){
                this_.changeToFailed(this_.getErrorMessage());
            }
        });
    },
    replaceNestedFormContents: function(newContents) {
        var this_ = this;
        var nestedForm = $('#'+this_.getNestedFormId());
        nestedForm.empty();
        nestedForm.append(newContents);
    },
    cancelUpload: function() {
	var this_ = this;
        if (this_.jqXhr) {
            this_.jqXhr.abort();
	    this_.jqXhr = undefined;
        } else {
	    this_.getFileInputPanel().cancelUpload(this_.getFilename())
        }
        $(this_.element).remove();
    },
    startUpload: function(submitName, ajaxOptions) {
        var this_ = this;
        $(this.element).append(this.createCancelButton().click(function(){
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
                        this_.getFileInputPanel().uploadFinished();
                        this_.changeToUploaded();
                    } else {
                        this_.replaceNestedFormContents(data.widget);
                        this_.getFileInputPanel().uploadFinished();
                    }
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
    changeFileInputToSingle: function(array, file) {
        if (array.length > 0) {
            var inputName = array[0].name;
            array.splice(0, array.length, {name:inputName, value:file});
        }
    },
    saveJqXhr: function(jqXhr) {
	this.jqXhr = jqXhr
    },
    changeToUploaded: function(){
        this.getProgressBar().replaceWith('');
        this.getCancelButton().replaceWith(this.createRemoveButton());
        this.state = 'uploaded';
    },
    changeToFailed: function(errorMessage){
        var errorLabel = $('<span class="has-danger text-help">'+errorMessage+'</span>');
        var formGroup = $(this.element).closest('.form-group');

        formGroup.addClass('has-danger');
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




