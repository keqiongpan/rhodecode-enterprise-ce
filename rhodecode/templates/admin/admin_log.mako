## -*- coding: utf-8 -*-
<%include file="/admin/admin_log_base.mako" />

<script type="text/javascript">
    $(function(){
        //because this is loaded on every pjax request, it must run only once
        //therefore the .one method
        $(document).on('pjax:complete',function(){
            show_more_event();
        });

        $(document).pjax('#user_log .pager_link', '#user_log');
    });
</script>

