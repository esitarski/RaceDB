from django import template
from django.template import Context, Template
from django.utils.safestring import mark_safe

register = template.Library()

tmpl = Template( '''{% spaceless %}
	<nav aria-label="Page navigation">
	  <ul class="pagination pagination-sm">
		{% if page.has_previous %}
			<li>
			  <a href="?page={{ page.previous_page_number }}" aria-label="Previous">
				<span aria-hidden="true">&laquo;</span>
			  </a>
			</li>
		{% else %}
			<li class="disabled"><span aria-hidden="true">&laquo;</span></li>
		{% endif %}
		{% for pn in paginator.page_range %}
			<li {% if pn == page.number %}class="active"{% endif %}><a href="?page={{pn}}">{{pn}}</a></li>
		{% endfor %}
		{% if page.has_next %}
			<li>
			  <a href="?page={{ page.next_page_number }}" aria-label="Next">
				<span aria-hidden="true">&raquo;</span>
			  </a>
			</li>
		{% else %}
			<li class="disabled"><span aria-hidden="true">&raquo;</span></li>
		{% endif %}
		<li class="disabled">&nbsp;&nbsp;{{paginator.count}}&nbsp;Total</li>
	  </ul>
	</nav>
	{% endspaceless %}''' )

@register.filter
def paginate_html( page ):
	return mark_safe(tmpl.render(Context({'page':page, 'paginator':page.paginator})))
