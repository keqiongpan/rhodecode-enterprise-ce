<%namespace name="base" file="/base/base.mako"/>

${c.comment_history.author.email}
${base.gravatar_with_user(c.comment_history.author.email, 16, tooltip=True)}
${h.age_component(c.comment_history.created_on)}
${c.comment_history.text}
${c.comment_history.version}