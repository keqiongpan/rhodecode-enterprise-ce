<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('{} Files Upload').format(c.repo_name)}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='repositories')}
</%def>

<%def name="breadcrumbs_links()"></%def>

<%def name="menu_bar_subnav()">
    ${self.repo_menu(active='files')}
</%def>

<%def name="main()">

<div class="box">
    ## Template for uploads
    <div style="display: none" id="tpl-dropzone">
        <div class="dz-preview dz-file-preview">
            <div class="dz-details">

                <div class="dz-filename">
                    <span data-dz-name></span>
                </div>
                <div class="dz-filename-size">
                    <span class="dz-size" data-dz-size></span>

                </div>

                <div class="dz-sending" style="display: none">${_('Uploading...')}</div>
                <div class="dz-response" style="display: none">
                    ${_('Uploaded')} 100%
                </div>

            </div>
            <div class="dz-progress">
                <span class="dz-upload" data-dz-uploadprogress></span>
            </div>

            <div class="dz-error-message">
            </div>
        </div>
    </div>

    <div class="edit-file-title">
        <span class="title-heading">${_('Upload new file')} @ <code>${h.show_id(c.commit)}</code></span>
        % if c.commit.branch:
        <span class="tag branchtag">
            <i class="icon-branch"></i> ${c.commit.branch}
        </span>
        % endif
    </div>

    <% form_url = h.route_path('repo_files_upload_file', repo_name=c.repo_name, commit_id=c.commit.raw_id, f_path=c.f_path) %>
    ##${h.secure_form(form_url, id='eform', enctype="multipart/form-data", request=request)}
    <div class="edit-file-fieldset">
        <div class="path-items">
            <ul>
            <li class="breadcrumb-path">
                <div>
                    <a href="${h.route_path('repo_files', repo_name=c.repo_name, commit_id=c.commit.raw_id, f_path='')}"><i class="icon-home"></i></a> /
                    <a href="${h.route_path('repo_files', repo_name=c.repo_name, commit_id=c.commit.raw_id, f_path=c.f_path)}">${c.f_path}</a> ${('/' if c.f_path else '')}
                </div>
            </li>
            <li class="location-path">

            </li>
            </ul>
        </div>

    </div>

    <div class="upload-form table">
        <div>

            <div class="dropzone-wrapper" id="file-uploader">
                <div class="dropzone-pure">
                    <div class="dz-message">
                    <i class="icon-upload" style="font-size:36px"></i></br>
                    ${_("Drag'n Drop files here or")} <span class="link">${_('Choose your files')}</span>.<br>
                    </div>
                </div>

            </div>
        </div>

    </div>

    <div class="upload-form edit-file-fieldset">
        <div class="fieldset">
            <div class="message">
                <textarea id="commit" name="message"  placeholder="${c.default_message}"></textarea>
            </div>
        </div>
        <div class="pull-left">
            ${h.submit('commit_btn',_('Commit changes'), class_="btn btn-small btn-success")}
        </div>
    </div>
    ##${h.end_form()}

    <div class="file-upload-transaction-wrapper" style="display: none">
    <div class="file-upload-transaction">
        <h3>${_('Commiting...')}</h3>
        <p>${_('Please wait while the files are being uploaded')}</p>
        <p class="error" style="display: none">

        </p>
        <i class="icon-spin animate-spin"></i>
        <p></p>
    </div>
    </div>

</div>

<script type="text/javascript">

    $(document).ready(function () {

        //see: https://www.dropzonejs.com/#configuration
        myDropzone = new Dropzone("div#file-uploader", {
            url: "${form_url}",
            headers: {"X-CSRF-Token": CSRF_TOKEN},
            paramName: function () {
                return "files_upload"
            }, // The name that will be used to transfer the file
            parallelUploads: 20,
            maxFiles: 20,
            uploadMultiple: true,
            //chunking: true, // use chunking transfer, not supported at the moment
            //maxFilesize: 2, // in MBs
            autoProcessQueue: false, // if false queue will not be processed automatically.
            createImageThumbnails: false,
            previewTemplate: document.querySelector('#tpl-dropzone').innerHTML,
            accept: function (file, done) {
                done();
            },
            init: function () {
                this.on("addedfile", function (file) {

                });

                this.on("sending", function (file, xhr, formData) {
                    formData.append("message", $('#commit').val());
                    $(file.previewElement).find('.dz-sending').show();
                });

                this.on("success", function (file, response) {
                    $(file.previewElement).find('.dz-sending').hide();
                    $(file.previewElement).find('.dz-response').show();

                    if (response.error !== null) {
                        $('.file-upload-transaction-wrapper .error').html('ERROR: {0}'.format(response.error));
                        $('.file-upload-transaction-wrapper .error').show();
                        $('.file-upload-transaction-wrapper i').hide()
                    }

                    var redirect_url = response.redirect_url || '/';
                    window.location = redirect_url

                });

                this.on("error", function (file, errorMessage, xhr) {
                    var error = null;

                    if (xhr !== undefined){
                        var httpStatus = xhr.status + " " + xhr.statusText;
                        if (xhr !== undefined && xhr.status >= 500) {
                            error = httpStatus;
                        }
                    }

                    if (error === null) {
                        error = errorMessage.error || errorMessage || httpStatus;
                    }

                    $(file.previewElement).find('.dz-error-message').html('ERROR: {0}'.format(error));
                });
            }
            });

        $('#commit_btn').on('click', function(e) {
            e.preventDefault();
            var button = $(this);
            if (button.hasClass('clicked')) {
                button.attr('disabled', true);
            } else {
                button.addClass('clicked');
            }

            var files = myDropzone.getQueuedFiles();
            if (files.length === 0) {
                alert("Missing files");
                e.preventDefault();
            }

            $('.upload-form').hide();
            $('.file-upload-transaction-wrapper').show();
            myDropzone.processQueue();

        });

    });

</script>
</%def>
