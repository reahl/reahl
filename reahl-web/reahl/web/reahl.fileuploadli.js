/* Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved. */
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
    return '<span class="reahl-button"><input type="submit" name="'+name+'" value="'+label+'" form="'+form_id+'"></span>';
}

$.widget('reahl.fileuploadli', {
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
        return this.options.fileInputPanel || $(this.element).closest('.reahl-file-upload-panel').data('reahl-fileuploadpanel');
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
        $(this.element).addClass('reahl-file-upload-li');
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
        return $(this.element).find('input[name^="event.remove_file"]').parent();
    },
    createFileNameSpan: function() {
        return $('<span>'+this.getFilename()+'</span>');
    },
    getFileNameSpan: function() {
        return $(this.element).find('span');
    },
    createProgressBar: function() {
        return $('<progress max=100>0%</progress>');
    },
    getProgressBar: function() {
        return $(this.element).find('progress');
    },
    createCancelButton: function() {
        return $(renderButton('cancel', this.getCancelLabel(), this.getFormId()));
    },
    getCancelButton: function() {
        return $(this.element).find('input[name="cancel"]').parent();
    },
    removeUploaded: function(ajaxOptions) {
        var this_ = this;
        this_.getFileInputPanel().clearFileInput();
        var data = {'_noredirect':''};
        data[this_.getRemoveButton().find('input').attr('name')] = '';
        $('#'+this.getFormId()).ajaxSubmit({
            data:  data,
            cache: false,
            beforeSubmit: function(a, form, options) {
            },
            success: function(data){
                this_.element.remove();
            },
            error: function(jqXHR, textStatus, errorThrown){
                this_.changeToFailed(this_.getErrorMessage());
            }
        });
    },
    startUpload: function(submitName, ajaxOptions) {
        $(this.element).append(this.createCancelButton());
        $(this.element).append(this.createFileNameSpan());
        $(this.element).append(this.createProgressBar());
        var this_ = this;
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
                    var result = $.parseJSON(data);
                    if (result.success) {
                        this_.changeToUploaded();
                    } else {
                        var nestedForm = $('#'+this_.getNestedFormId());
                        nestedForm.empty();
                        nestedForm.append(result.widget);
                        this_.getFileInputPanel().uploadFinished();
                    }
                },
                error: function(jqXHR, textStatus, errorThrown){
                    this_.changeToFailed(this_.getErrorMessage());
                },
                uploadProgress: function(event, position, total, percentComplete){
                    this_.updateProgress(percentComplete);
                }
            });
        };
        this_.getFileInputPanel().uploadStarted(startThisUpload);
    },
    changeFileInputToSingle: function(array, file) {
        if (array.length > 0) {
            var inputName = array[0].name;
            array.splice(0, array.length, {name:inputName, value:file});
        };
    },
    saveJqXhr: function(jqXhr) {
        var this_ = this;
        this.getCancelButton().find('input').click(function(){
            jqXhr.abort();
            $(this_.element).remove();
            return false;
        });
    },
    changeToUploaded: function(){
        this.getFileInputPanel().uploadFinished();
        this.getProgressBar().replaceWith('');
        this.getCancelButton().replaceWith(this.createRemoveButton());
        this.state = 'uploaded';
    },
    changeToFailed: function(errorMessage){
        this.getFileInputPanel().uploadFinished();
        var errorLabel = $('<label class="error">'+errorMessage+'</label>');

        if (this.state === 'uploaded' ) {
            $(this.element).append(errorLabel);
            this.getRemoveButton().find('input').prop('disabled', true);
        } else {
            this.getProgressBar().replaceWith(errorLabel);
            this.getCancelButton().find('input').prop('disabled', true);
        };
        this.state = 'failed';
    },
    updateProgress: function(percentComplete){
        this.getProgressBar().attr('value', percentComplete);
        this.getProgressBar().html(percentComplete+'%');
    },

});

$.extend($.reahl.fileuploadli, {
    version: '1.8'
});

})(jQuery);




