"use strict"

function pDistanceSquared(x, y, x1, y1, x2, y2) {
	const A = x - x1, B = y - y1, C = x2 - x1, D = y2 - y1;

	const dot = A * C + B * D;
	const len_sq = C * C + D * D;
	let param = -1;
	if (len_sq != 0) // 0 length line
	  param = dot / len_sq;

	let xx, yy;

	if (param < 0) {
		xx = x1;
		yy = y1;
	}
	else if (param > 1) {
		xx = x2;
		yy = y2;
	}
	else {
		xx = x1 + param * C;
		yy = y1 + param * D;
	}

	const dx = x - xx, dy = y - yy;
	return dx * dx + dy * dy;
}

function gap_format( t, show_minutes=true ) {
	t = Math.abs( t );
	const s = Math.trunc( t );
	const f = t - s;
	const m = Math.trunc(s / 60) % 60;
	const h = Math.trunc( s / (60*60) );
	
	let text = [];
	if( h ) {
		text.push( h );
		show_minutes = true;
	}
	if( m || show_minutes ) {
		text.push( (m < 10 ? '0' : '') + m );
		const sf = s % 60;
		text.push( (sf < 10 ? '0' : '') + sf );
	}
	else {
		const sf = (s % 60) + f;
		text.push( (sf < 10 ? '0' : '') + sf.toFixed(2) );
	}
	return text.join(':');	
}

function spread_labels( p, h, y_min, y_max ) {
	// Spread labels out so they don't overlap.
	// p is an array of points, h is the height of the label text.
	// p must be sorted in increasing order.
	// y_min and y_max are the limits.
	// Returns an array of centered text y-values.
	
	const h2 = h / 2;
	
	// Use floating point comparisons based on a tolerance rather than direct comparisons.
	// This makes us tolerant of numerical instability.
	const tolerance = 0.00001;
	function gt( a, b ) { return a - b > tolerance; }
	function lt( a, b ) { return b - a > tolerance; }
	
	// Start by putting all labels equal to the starting position.
	let y = p.map( (v) => v );
	
	for( let k = 0; k < p.length; ++k ) {
		
		// Check for overlapping positions.
		let a, b, c;
		for( b = 1; b < p.length; ++b ) {
			if( gt( y[b-1] + h, y[b] ) )
				break;
		}
		
		if( b == p.length )
			break;	// No conflicts.  We are done.
			
		// Find the start the preceding adjacent group before the conflict.
		for( a = b-1; a > 0; --a ) {
			if( lt(y[a-1] + h, y[a]) )
				break;
		}
		
		// Find the rest of the conflict positions, including the succeeding adjacent group if there is one.
		for( c = b + 1; c < p.length; ++c ) {
			if( lt(y[c-1] + h, y[c]) )
				break;
		}
			
		// Minimize the least-squares sum to get the best label spread.
		const n = c - a;
		let s = 0;
		for( let i = a; i < c; ++i )
			s += p[i] - h * (i - a);

		// Compute the top of the spread-out group and constrain to y_min, y_max.
		const y_best = Math.max( y_min + h2, Math.min( s/n, y_max - n*h - h2) );
			
		// Update the label positions.
		for( let i = a; i < c; ++i )
			y[i] = y_best + h * (i-a);
	}
	return y;
}

class Rider {
	constructor( bib, race_times, color, info ) {
		this.bib = bib;
		this.race_times = race_times;
		this.color = color;
		this.info = info;
	}
	
	get_text( width=1000 ) {
		let name = [];
		if( this.info.LastName ) name.push( this.info.LastName );
		if( this.info.FirstName ) name.push( width < 800 ? this.info.FirstName.slice(0,1).toUpperCase() + '.' : this.info.FirstName );
		const name_text = name.join( ', ' );
		let text = [this.bib];
		if( name_text )
			text.push( name_text );
		return text.join( ' ' );
	}
}

class GapChart {
	constructor( canvas, payload ) {
		this.rider_select = null;
		this.x_gap = null;
		this.y_gap = null;
		this.gap = null;
		this.moveTimer = null;
		this.x_mouse = -1;
		this.y_mouse = -1;

		
		// From http://tools.medialab.sciences-po.fr/iwanthue/
		this.line_colors = [
			"#3A3312",
			"#9756EF",
			"#00D222",
			"#69D2FD",
			"#F04403",
			"#FE3D94",
			"#0EAB6E",
			"#301F5B",
			"#CDA303",
			"#2C6900",
			"#45DD97",
			"#E8B8A4",
			"#D629BD",
			"#0AA2A1",
			"#C30043",
			"#53131A",
			"#784B07",
			"#395B8F",
			"#284299",
			"#F4B478",
			"#993AAE",
			"#13A3E7",
			"#340631",
			"#F25DEE"
		];
		
		this.lapLineColour = '#B0B0B0';
		this.positionBackgroundColour = '#B7B7B7';
		this.positionHorizontalLineColor = '#B9B9B9';
		
		this.topCornerBackgroundColour = '#8E8C8D';
		this.legendBackgroundColour = '#C8C8C8';
		this.lappedBackgroundColour = '#D8E6F4';
		
		this.lapLabelBorderColour = '#707070';
		this.primeColour = '#FFFFAA';
		this.deselectedLine = 'rgb(200,200,200)';
		
		this.set_payload( payload );
		
		this.canvas = canvas;
		this.canvas.addEventListener( 'mousemove', this.onMouseMove.bind(this) );
		
		this.draw();
	}
	
	doMouseMove( evt ) {
		const rect = this.canvas.getBoundingClientRect();
		const x = evt.clientX - rect.left, y = evt.clientY - rect.top;
		this.x_mouse = x;
		this.y_mouse = y;
		
		const [rider_select_old, x_gap_old, y_gap_old, gap_old] = [this.rider_select, this.x_gap, this.y_gap, this.gap];
		[this.x_gap, this.y_gap, this.gap, this.rider_select] = this.get_rider_gap( x, y );

		if( this.rider_select !== rider_select_old || this.x_gap !== x_gap_old || this.y_gap !== y_gap_old || this.gap !== gap_old )
			this.draw();
	}
	
	onMouseMove( evt ) {
		// Only process the move event if the mouse stops moving for a bit.
		if( this.moveTimer ) {
			this.rider_select = null;
			clearTimeout( this.moveTimer );
		}
		let that = this;
		this.moveTimer = setTimeout( function() { that.doMouseMove(evt); that.moveTimer=null; }, 10 );
	}
	
	onResize( evt ) {
		this.canvas.width = window.innerWidth;
		this.canvas.height = window.innerHeight;
		this.rider_select = null;
		this.draw();
	}
	
	set_payload( payload ) {
		this.category_name = payload.catDetails[0].name;
		
		let riders = [];
		let lap_max = 0;
		let start_min = +Infinity;
		for( const [bib,info] of Object.entries(payload.data) ) {
			if( info.raceTimes && info.raceTimes.length >= 2 && info.status !== 'DNS' ) {
				riders.push( new Rider(
						Number(bib),
						info.raceTimes,
						this.line_colors[riders.length % this.line_colors.length],
						{'FirstName':info.FirstName, 'LastName':info.LastName}
					)
				);
				lap_max = Math.max( lap_max, info.raceTimes.length );
				start_min = Math.min( start_min, info.raceTimes[0] );
			}
		}
		// Remove any common start offset.
		if( start_min > 0.0 ) {
			for( let r of riders ) {
				for( let i = 0; i < r.race_times.length; ++i )
					r.race_times[i] -= start_min;
			}
		}
		this.riders = riders;
		
		let lap_leader_time = Array.from( {length: lap_max}, () => +Infinity );
		for( let r of riders ) {
			for( let i = 0; i < r.race_times.length; ++i )
				lap_leader_time[i] = Math.min( lap_leader_time[i], r.race_times[i] );
		}
		
		let lap_data = Array.from( lap_leader_time, () => new Map() );
		
		let gap_max = 0;
		lap_leader_time.push( +Infinity );		// Add a backstop time so we don't need to check for array end.
		for( let r of riders ) {
			let j = 0;
			for( let i = 0; i < r.race_times.length; ++i ) {
				// Find the leader's lap the rider is in.
				for( ; ; ++j ) {
					if( lap_leader_time[j+1] > r.race_times[i] )
						break;
				}
				const gap = r.race_times[i] - lap_leader_time[j];
				gap_max = Math.max( gap_max, gap );
				lap_data[j].set( r.bib, [gap, r] );
			}
		}
		
		this.gap_max = gap_max;
		this.lap_data = lap_data;
		lap_leader_time.pop();		// Remove the backstop.
		this.lap_leader_time = lap_leader_time;
	}
	
	get_segment( bib, i ) {
		// Get the segment for the give bib starting at lap i.
		let v = this.lap_data[i].get( bib );
		if( v === undefined )
			return [undefined, undefined, undefined, undefined, undefined];
		let [gap, r] = v;
		const x0 = this.get_x( i ), y0 = this.get_y( gap );

		let i_next;
		for( i_next = i + 1; i_next < this.lap_data.length; ++i_next ) {
			v = this.lap_data[i_next].get( bib );
			if( v !== undefined )
				break;
		}
		if( v === undefined )
			return [undefined, undefined, undefined, undefined, undefined];
		[gap, r] = v;
		const x1 = this.get_x( i_next ), y1 = this.get_y( gap );
		return [x0, y0, x1, y1, i_next];
	}
	
	get_rider_gap( x, y ) {
		// Find the closest line to the coordinate.
		let lap = this.get_lap( x );
		let d_best = +Infinity;
		let r_best, gap_best;
		let x_gap, y_gap;
		if( this.x_left <= x && this.y_top <= y && y < this.y_bottom ) {
			for( let [x0,y0,x1,y1,r] of this.lap_lines[lap] ) {
				const d = pDistanceSquared( x, y, x0, y0, x1, y1 );
				if( d < d_best ) {
					d_best = d;
					r_best = r;
					if( x-x0 < x1-x ) {
						x_gap = x0;
						y_gap = y0;
					}
					else {
						x_gap = x1;
						y_gap = y1;
					}
				}
			}
		}
		const gap = r_best === undefined ? 0 : this.get_gap(y_gap);
		return [x_gap, y_gap, gap, r_best];
	}
	
	draw_bib_line( r, ctx ) {
		ctx.lineWidth = 4;
		if( !this.rider_select || this.rider_select === r )
			ctx.strokeStyle = r.color;
		else
			ctx.strokeStyle = this.deselectedLine;
		
		let path_length = 0;
		let i, y_last;
		for( i = 0; i < this.lap_data.length - 1; ) {
			let [x0, y0, x1, y1, i_next] = this.get_segment( r.bib, i );
			if( path_length === 0 ) {
				ctx.beginPath();
				ctx.moveTo( x0, y0 );
			}
			if( i_next === i+1 ) {
				ctx.bezierCurveTo( (x0+x1)/2, y0, (x0+x1)/2, y1, x1, y1 );
				++path_length;
			}
			else {
				// Rider was lapped.
				
				// Flush the path to this point.
				ctx.stroke();
				
				// Draw a dashed line
				ctx.beginPath();
				ctx.moveTo( x0, y0 );
				ctx.bezierCurveTo( (x0+x1)/2, y1, (x0+x1)/2, y1, x1, y1 );				
				
				ctx.setLineDash( [2,10] );
				ctx.stroke();
				ctx.setLineDash( [] );
				path_length = 0;
			}
			
			// Record the lines by lap so we can select them later.
			for( let j = i; j < i_next; ++j )
				this.lap_lines[j].push( [x0,y0,x1,y1,r] );
			
			y_last = y1;
			i = i_next;
		}
		
		// Stroke the final path.
		if( path_length )
			ctx.stroke();
		return [i, y_last];	// Return gap position of the last lap.
	}
	
	get_x( lap ) { return this.x_left + (lap + 0.5) * this.lap_scale; }
	get_lap( x ) {
		const lap = Math.trunc((x - this.x_left - 0.5 * this.lap_scale) / this.lap_scale);
		return Math.max( 0, Math.min(lap, this.lap_lines.length-1) );
	}
	get_y( gap, y_top_offset=true ) { return this.y_top + (y_top_offset ? this.y_top_offset : 0) + gap * this.gap_scale; }
	get_gap( y, y_top_offset=true ) { return (y - this.y_top - (y_top_offset ? this.y_top_offset : 0)) / this.gap_scale; }
	
	draw() {
		let width = this.canvas.width, height = this.canvas.height;
		
		const ctx = this.canvas.getContext("2d");
		
		function line( x0, y0, x1, y1 ) {
			ctx.beginPath();
			ctx.moveTo( x0, y0 );
			ctx.lineTo( x1, y1 );
			ctx.stroke();
		}
		
		// Clear the screen.
		ctx.fillStyle = '#FFFFFF';
		ctx.fillRect( 0, 0, width, height );
		
		const gap_max = Math.max( 1.0, this.gap_max );
		
		// Get a reasonable tick mark.
		const ticks = [0.1, 0.2, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 2*60.0, 5*60.0, 10*60.0, 15*60.0, 30*60, 60*60, 2*60.0, 5*60.0, 10*60.0, 24*60.0];
		let tick = ticks[ticks.length-1];
		for( let i = 1; i < ticks.length; ++i ) {
			if( gap_max / ticks[i] < 4 ) {
				tick = ticks[i-1];
				break;
			}
		}
		this.show_minutes = (gap_max >= 60);
		
		const lap_num_height = height / 50;
		const label_font = (lap_num_height * 0.8) + 'px Arial';
		
		this.y_top = lap_num_height * 3;
		this.y_top_offset = lap_num_height;
		this.y_bottom = height - lap_num_height * 2.5;
		this.gap_scale = (this.y_bottom - this.y_top - this.y_top_offset) / gap_max;

		this.row_height = Math.min( lap_num_height * 0.8, (this.y_bottom - this.y_top) / this.riders.length );
		const info_font = this.row_height + 'px Arial';
		const font_height = this.row_height;
		
		ctx.font = label_font;
		const label_margin = ctx.measureText( '  ' ).width;
		this.x_left = 0;
		for( let i = 0; i*tick < gap_max; ++i )
			this.x_left = Math.max( this.x_left, ctx.measureText( gap_format(i*tick, this.show_minutes) ).width + label_margin * 2 );
		
		ctx.font = info_font;
		this.label_offset = ctx.measureText('      ').width;
		this.x_right = width;
		for( let r of this.riders )
			this.x_right = Math.min( this.x_right, width - ctx.measureText(r.get_text(width)).width );
		
		this.lap_scale = (this.x_right - this.x_left) / (this.lap_leader_time.length);
		
		// Draw the border lines and legend.
		ctx.lineWidth = 1;
		
		// Draw the legend background.
		ctx.fillStyle = this.legendBackgroundColour;
		ctx.fillRect( 0, this.get_y(0, false) - lap_num_height*1.5, width, lap_num_height*1.5 );
		ctx.fillRect( 0, this.get_y(0, false) - lap_num_height*1.5, this.x_left, height - this.y_top );
		ctx.fillRect( 0, height - lap_num_height*1.5, width, lap_num_height*1.5 );
		
		// Draw the left side legend.
		ctx.font = label_font;
		ctx.fillStyle = '#000000';
		ctx.strokeStyle = '#000000';
		ctx.textBaseline = 'middle';
		ctx.textAlign = 'right';
		for( let i = 0; i*tick < gap_max; ++i ) {
			const y = this.get_y( i*tick );
			line( this.x_left-label_margin/2, y, this.x_left+label_margin/2, y );
			ctx.fillText( gap_format(i*tick, this.show_minutes), this.x_left - label_margin, y );
		}
		
		// Draw the lap lines.
		ctx.lineWidth = 1;
		ctx.strokeStyle = this.lapLineColour;
		for( let lap = 0; lap < this.lap_leader_time.length; ++lap ) {
			const x = this.get_x( lap - 0.5);
			line( x, this.y_top, x, this.y_bottom );
		}
		
		// Draw the lap numbers.
		const lap_width = this.lap_scale;
		ctx.font = label_font;
		ctx.textAlign = 'center';
		ctx.textBaseline = 'bottom';
		ctx.lineWidth = 1;
		ctx.setLineDash( [] );
		let xLast = 0;
		for( let lap = 0; lap < this.lap_leader_time.length; ++lap ) {
			const lap_str = ' ' + (this.lap_leader_time.length - lap - 1) + ' ';
			const t_width = ctx.measureText(lap_str).width;
			const x_middle = this.get_x(lap) + lap_width/2;
			if( x_middle + t_width / 2 < xLast )
				continue;
			
			const x = this.get_x(lap), y = this.get_y(0, false) - lap_num_height * 1.25;
			ctx.beginPath()
			ctx.moveTo( x - t_width/2, y );
			ctx.lineTo( x + t_width/2, y );
			ctx.lineTo( x + t_width/2, y + lap_num_height );
			ctx.lineTo( x, y + lap_num_height * 1.25 );
			ctx.lineTo( x - t_width/2, y + lap_num_height );
			ctx.closePath();
			
			ctx.fillStyle = '#FFFFFF';
			ctx.fill();
			ctx.strokeStyle = this.lapLabelBorderColour;
			ctx.stroke();
			
			ctx.fillStyle = '#000000';
			ctx.fillText( lap_str, x, this.get_y(0, false) - lap_num_height * 0.25);
			xLast = x_middle - t_width/2 - 2;
		}	

		this.lap_lines = Array.from( this.lap_leader_time, () => [] );	// Array of lines from or passing through this lap.
		
		// Draw the gap for each rider.  Keep track of the final lap gap.
		ctx.lineCap = 'round';
		let finish_gap = Array.from( {length:this.lap_leader_time.length+1}, () => [] );
		for( let r of this.riders ) {
			const [i, y_last] = this.draw_bib_line( r, ctx );
			if( i !== undefined )
				finish_gap[i].push( [y_last, r] );
		}
		if( this.rider_select )
			this.draw_bib_line( this.rider_select, ctx );
		
		// Draw the labels on the gaps.
		ctx.fillStyle = '#000000';
		ctx.font = info_font;
		ctx.textBaseline = 'middle';
		ctx.textAlign = 'left';
		ctx.lineWidth = 1;
		//ctx.strokeStyle = this.lapLineColour;
		ctx.strokeStyle = '#000000';
		for( const [i, fg] of finish_gap.entries() ) {
			if( fg.length === 0 )
				continue;
			
			fg.sort( (a, b) => a[0] - b[0] );	// Sort by increasing gap offset.
			const y_spread = spread_labels( Array.from(fg, (v) => v[0]), this.row_height, this.get_y(0)-lap_num_height*.5, this.y_bottom );
			const x0 = this.get_x(i);
			const x1 = x0 + this.label_offset;
			const xh = (x0 + x1) / 2;

			for( let g = 0; g < fg.length; ++g ) {
				// Draw the indicator line to the text.
				const [y_last, r] = fg[g];
				if( this.rider_select ) {
					if( this.rider_select === r ) {
						ctx.fillStyle = '#000000';
						ctx.strokeStyle = '#000000';
					}
					else {
						ctx.fillStyle = this.deselectedLine;
						ctx.strokeStyle = this.deselectedLine;
					}
				}
				else {
					ctx.fillStyle = '#000000';
					ctx.strokeStyle = '#000000';
				}
				
				ctx.beginPath()
				ctx.moveTo( x0, y_last );
				const y_to = y_spread[g];
				//ctx.bezierCurveTo( xh, y_last, xh, y_to, x1, y_to );
				ctx.lineTo( x1, y_to );
				ctx.stroke();
				
				// Draw the text.
				const text = r.get_text(width);
				ctx.fillText( text, x1, y_spread[g] );
			}
		}
		
		if( this.rider_select ) {
			// Draw the callouts.
			const text_co = gap_format( this.gap, this.show_minutes ) + ': ' + this.rider_select.get_text();
			const x_co = this.x_gap, y_co = this.y_gap + lap_num_height;
			
			ctx.strokeStyle = '#000000';
			ctx.fillStyle = '#FFFF99';
			ctx.beginPath()
			ctx.roundRect( x_co - lap_num_height/2, y_co - lap_num_height/2, ctx.measureText(text_co).width + lap_num_height, lap_num_height*1.5, lap_num_height/2 );
			ctx.fill();
			ctx.stroke();
			
			ctx.font = label_font;
			ctx.textBaseline = 'top';
			ctx.textAlign = 'left';
			ctx.fillStyle = '#000000';
			ctx.fillText( text_co, x_co, y_co );
			
			ctx.lineWidth = 1;
			line( x_co, this.y_gap, x_co, y_co );
		}
		
		// Draw the category name.
		ctx.textAlign = 'left';
		ctx.textBaseline = 'bottom';
		ctx.font = label_font;
		ctx.fillStyle = '#000000';
		ctx.fillText( this.category_name, lap_num_height*.75, lap_num_height*1.25 );
	}
}
