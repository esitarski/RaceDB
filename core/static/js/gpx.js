"use strict";

const grad_speed = [
 2.217527336052238,
 2.202853110275395,
 2.188053909555161,
 2.1731282463704,
 2.158074603708304,
 2.142891434526821,
 2.1275771612501315,
 2.1121301753048813,
 2.096548836705969,
 2.0808314737019544,
 2.06497638249156,
 2.0489818270244,
 2.032846038900783,
 2.016567217387692,
 2.000143529570188,
 1.9835731106603496,
 1.966854064488727,
 1.9499844642068176,
 1.93296235323291,
 1.915785746478052,
 1.8984526318939003,
 1.880960972389858,
 1.8633087081732884,
 1.8454937595738268,
 1.8275140304210298,
 1.8093674120537766,
 1.7910517880503405,
 1.772565039779714,
 1.7539050528880413,
 1.7350697248488745,
 1.7160569737225158,
 1.6968647482884063,
 1.6774910397351455,
 1.6579338951157376,
 1.6381914328010398,
 1.6182618601922334,
 1.598143493983527,
 1.5778347832992043,
 1.5573343360641365,
 1.5366409490040733,
 1.5157536417102468,
 1.4946716952416133,
 1.4733946957759005,
 1.4519225838553647,
 1.430255709802776,
 1.4083948959035018,
 1.3863415059564836,
 1.3640975227843928,
 1.3416656342536257,
 1.3190493282790055,
 1.2962529971645702,
 1.2732820514472172,
 1.250143043148757,
 1.2268437979867222,
 1.2033935556271051,
 1.179803116464806,
 1.1560849926753485,
 1.132253560384181,
 1.1083252087489648,
 1.0843184805615627,
 1.0602541976891038,
 1.036155563355384,
 1.0120482320197688,
 0.9879603365842997,
 0.9639224620353721,
 0.9399675546183934,
 0.9161307564793237,
 0.8924491575934091,
 0.868961459883586,
 0.8457075527404815,
 0.8227280045610927,
 0.8000634810946754,
 0.7777541077897695,
 0.755838799278375,
 0.7343545838357127,
 0.7133359533865637,
 0.6928142698501474,
 0.6728172560960906,
 0.6533685946811283,
 0.6344876503870627,
 0.6161893242166845,
 0.598484037903228,
 0.581377840100501,
 0.5648726190130284,
 0.548966401780926,
 0.5336537186160659,
 0.518926009368216,
 0.5047720515425184,
 0.49117839133466934,
 0.4781297625120825,
 0.4656094815064962,
 0.45359981054187487,
 0.44208228375211506,
 0.43103799389939434,
 0.42044783942572794,
 0.410292733162104,
 0.400553775128795,
 0.3912123925580405,
 0.3822504506358954,
 0.37365033757169774,
 0.3653950275316242,
 0.35746812477661477,
 0.34985389207223583,
 0.34253726612546037,
 0.3355038624776109,
 0.3287399719624444,
 0.3222325505357491,
 0.31596920400500406,
 0.3099381689382677,
 0.30412829081150256,
 0.29852900026236706,
 0.2931302881543721,
 0.2879226800158578,
 0.28289721030091614,
 0.27804539682146806,
 0.27335921561865145,
 0.2688310764750952,
 0.2644537992153579,
 0.26022059089788563,
 0.2561250239665933,
 0.25216101540213737,
 0.24832280689087236,
 0.2446049460123153,
 0.24100226843277156,
 0.2375098810828684,
 0.23412314628945793
];

Array.prototype.last = function() {
    return this[this.length - 1];
}

function radians( deg ) { return (deg * Math.PI) / 180.0; }

function distance_adjustment( distance, elevation ) {
	const gradient = elevation / distance;
	const i = Math.trunc( ((gradient + 0.25) / 0.5) * grad_speed.length );
	return distance / grad_speed[Math.max( 0, Math.min(i, grad_speed.length-1) )];
}

function vec_minmax( a ) {
	let v_min = [...a[0]], v_max = [...a[0]];
	for( const v of a ) {
		for( let j = 0; j < v.length; ++j ) {
			if( v[j] < v_min[j] )	v_min[j] = v[j];
			if( v_max[j] < v[j] )	v_max[j] = v[j];
		}
	}	
	return [v_min, v_max];
}

function modf( v ) {
	const s = Math.sign( v );
	if( s < 0 )
		v *= -1;
	const i = Math.trunc( v )
	const f = v - i;
	return [s*f, s*i];
}

function fract( v ) {
	return modf(v)[0];
}

const EARTH_RADIUS = 6371.0088 * 1000.0;	// meters

function great_circle_distance( pointA, pointB ) {
	const [latA, lonA] = pointA;
	const [latB, lonB] = pointB;
	const phiA = radians( latA );
	const phiB = radians( latB );
	const delta_latitude = radians(latB - latA);
	const delta_longitude = radians(lonB - lonA);
	const a = (
		Math.pow(Math.sin(delta_latitude / 2.0), 2)
		+ Math.cos(phiA) * Math.cos(phiB) * Math.pow( Math.sin(delta_longitude / 2.0), 2 )
	);
	const c = 2.0 * Math.atan2(Math.sqrt(a), Math.sqrt(Math.max(0.0, 1.0 - a)));
	return EARTH_RADIUS * c;
}

function fw( n, w ) {
	return n.toString().padStart( w, "0" );
}

function format_t( t ) {
	let [f, s] = modf( t );
	const h = Math.trunc( s / (60*60) );
	const m = Math.trunc( s / 60) % 60;
	s = (s % 60) + f;
	return h + ':' + fw(m,2) + ':' + fw(s.toFixed(2), 5);
}

function binary_search( arr, v ) {
	let lo = 0, hi = arr.length;
	while( lo < hi) {
		const mid = Math.trunc( (lo + hi) / 2 );
		if( arr[mid] < v )
			lo = mid + 1;
		else
			hi = mid;
	}
	return lo;
}

function* zip(...arrays) {
	const minLength = arrays.reduce( (min, curIterable) => curIterable.length < min ? curIterable.length: min, +Infinity );
	for( let i = 0; i < minLength; i++ )
		yield arrays.map(a => a[i]);
}

function pos_mod( v, m ) {
	const x = v % m;
	return x < 0.0 ? (x + m) : x;
}

function overlaps( r1, r2 ) {
	// Check if two rectangles overlap.
	//                                     0,  1,  2,  3
	// Rectangles are arrays of the form [x1, y1, x2, y2].
	//     r1.x1 <= r2.x2 && r2.x1 <= r1.x2 && r1.y1 <= r2.y2 && r2.y1 <= r1.y2
	return r1[0] <= r2[2] && r2[0] <= r1[2] && r1[1] <= r2[3] && r2[1] <= r1[3];
}

function mulberry32( a ) {
	return function() {
		var t = a += 0x6D2B79F5;
		t = Math.imul(t ^ t >>> 15, t | 1);
		t ^= t + Math.imul(t ^ t >>> 7, t | 61);
		return ((t ^ t >>> 14) >>> 0) / 4294967296;
	}
}
var rnd = mulberry32( 0xed );
	
class Course {
	constructor( lat_lon_elevation, is_loop=true, first_lap_distance=null, lap_distance=null ) {
		this.reset();
		
		this.is_loop = is_loop;							// True if the course is a loop, otherwise point-to-point.
		this.first_lap_distance = first_lap_distance;	// first lap distance in (m)
		this.lap_distance = lap_distance;				// lap distance in (m)

		this.set_lat_lon_elevation( lat_lon_elevation );
	}
	
	reset() {
		this.cum_distance = [];		// Cumulative distance over the entire course using adjusted distance.
		this.heading = [];			// Heading of each line segment in radians.
		this.graident = [];			// Gradient of each segment
		this.elevation = [];		// Elevation
		this.altigraph = [];		// distance, elevation (non-adjusted distance)
		this.points = [];			// Flat earth coordinates in meters
		this.max_gradient = 0.0;

		this.x_min = 0.0;
		this.x_max = 0.0;
		this.y_min = 0.0;
		this.y_max = 0.0;
		this.elevation_min = 0.0;
		this.elevation_max = 0.0;
		
		// Offsets for finish and start line.
		this.finish_dx = null;
		this.finish_dy = null;
		this.start_dx = null;
		this.start_dy = null;
	}
	
	set_lat_lon_elevation( lat_lon_elevation ) {
		this.reset();
		if( !lat_lon_elevation || !lat_lon_elevation.length ) {
			return;
		}
		
		// Use a flat earth model.
		const [[lat_min, lon_min, e_min],[lat_max, lon_max, e_max]] = vec_minmax( lat_lon_elevation);
		this.elevation_min = e_min;
		this.elevation_max = e_max;
						
		let degree_delta = (lat_max - lat_min) / 10.0;
		const lat_distance = great_circle_distance( [lat_min, lon_min], [lat_min+degree_delta, lon_min] ) / degree_delta;
		degree_delta = (lon_max - lon_min) / 10.0;
		const lon_distance = great_circle_distance( [lat_min, lon_min], [lat_min, lon_min+degree_delta] ) / degree_delta;
		
		this.points = lat_lon_elevation.map( function(v) { let [lat, lon, e] = v; return [(lon - lon_min) * lon_distance, (lat - lat_min) * lat_distance]; } );
		// Flip the points as draw works from top to bottom on the screen.
		for( let i = 0; i < this.points.length; ++i )
			this.points[i][1] = this.y_max-this.points[i][1];		
		[[this.x_min, this.y_min], [this.x_max, this.y_max]] = vec_minmax( this.points );
		this.elevation = lat_lon_elevation.map( (v) => v[2] );

		this.size = [this.x_max - this.x_min, this.y_max - this.y_min];
		
		const tree_factor = 1.4;
		const tree_size = this.size.map( (v) => v*tree_factor );
		const tree_min = [this.x_min - tree_size[0] * (tree_factor-1)/2, this.y_min - tree_size[1] * (tree_factor-1)/2];
		this.tree_points = Array.from( { length:256 }, () => [tree_min[0] + rnd()*tree_size[0], tree_min[1] + rnd()*tree_size[1]] );
		
		// Make a points loop if required for drawing.
		this.course_points = this.points.map( (x) => x );
		if( this.is_loop )
			this.course_points.push( this.course_points[0] );
		
		// Cumulative distance (elevation adjusted distance).
		this.cum_distance = [0.0];
		const i_max = this.is_loop ? this.points.length : this.points.length - 1;
		for( let i = 0; i < i_max; ++i )
			this.cum_distance.push( this.cum_distance.last() + this.segment_distance(i) );
		if( !this.lap_distance )
			this.lap_distance = this.cum_distance.last();
			
		// Heading by segment.
		// Gradient by segment.
		this.heading = [];
		this.gradient = [];
		this.min_gradient = +Infinity;
		this.max_gradient = -Infinity;
		for( let i = 0; i < i_max; ++i ) {
			const heading = this.segment_heading(i), gradient = this.segment_gradient(i);
			this.heading.push( heading );
			this.gradient.push( gradient );
			if( this.min_gradient > gradient ) this.min_gradient = gradient;
			if( this.max_gradient < gradient ) this.max_gradient = gradient;
		}
	
		// Altigraph (non-adjusted distance, elevation, gradient)
		this.altigraph = [[0.0, this.elevation[0], this.segment_gradient(0)]];
		for( let i = 1; i < this.points.length; ++i ) {
			const [p0, p1] = this.segment( i-1 );
			const d = Math.sqrt( Math.pow(p0[0]-p1[0],2) + Math.pow(p0[1]-p1[1],2) )		// Unadjusted distance.
			this.altigraph.push( [this.altigraph.last()[0] + d, this.elevation[i], this.segment_gradient(i)] )
		}
		
		// Finish and Start Line offsets.
		if( this.is_loop ) {
			let heading = this.heading[0] + Math.PI/2.0;
			this.finish_dx = Math.cos(heading);
			this.finish_dy = Math.sin(heading);
		}
		else {
			let heading = this.heading[0] + pi/2.0;
			this.start_dx = Math.cos(heading);
			this.start_dy = Match.sin(heading);
			
			heading = this.heading.last() + pi/2.0;
			this.finish_dx = Math.cos(heading);
			this.finish_dy = Math.sin(heading);
		}
		
		// Locate some sheep spectators at the finish.
		const x_sheep = this.points[0][0] + this.finish_dx * tree_size[0]/15;
		const y_sheep = this.points[0][1] + this.finish_dy * tree_size[0]/15;
		this.sheep_points = Array.from( { length:3 }, () => [x_sheep + rnd()*tree_size[0]/50, y_sheep + rnd()*tree_size[0]/50] );
	}
		
	segment( i ) {
		let j = 0;
		if( i >= this.points.length - 1 ) {
			if( this.is_loop ) {
				i = this.points.length - 1;
				j = 0;
			}
			else {
				i = this.points.length - 2;
				j = i + 1;
			}
		}
		else
			j = i + 1;
		return [this.points[i], this.points[j]];
	}

	segment_distance( i ) {
		const [p0, p1] = this.segment( i );
		let d = Math.sqrt( Math.pow(p0[0]-p1[0],2) + Math.pow(p0[1]-p1[1],2) );
		// Adjust the distance based on the change in elevation to better estimate climbs/descents.
		d = distance_adjustment( d, this.elevation[(i+1)%this.points.length] - this.elevation[i] );
		return d;
	}
	
	segment_gradient( i ) {
		const [p0, p1] = this.segment( i );
		// Unadjusted distance.
		let d = Math.sqrt( Math.pow(p0[0]-p1[0],2) + Math.pow(p0[1]-p1[1],2) );
		return (this.elevation[(i+1)%this.elevation.length] - this.elevation[i%this.elevation.length]) / d;
	}
	
	adjusted_distance() { return this.cum_distance.last(); }
		
	segment_heading( i ) {
		// heading on segment i
		const [p0, p1] = this.segment( i );
		return Math.atan2( p1[1] - p0[1], p1[0] - p0[0] );
	}
		
	i_from_d( d, i_hint=0 ) {
		d = pos_mod( d, this.cum_distance.last() );
		i_hint = Math.min( Math.max(i_hint, 0), this.cum_distance.length-2 );
		// Check if i_hint contains the segment with the given distance.
		if( !(this.cum_distance[i_hint] <= d && d < this.cum_distance[i_hint+1]) ) {
			// If not, check if the next segment has it.
			i_hint = (i_hint + 1) % (this.cum_distance.length-2);
			if( !(this.cum_distance[i_hint] <= d && d < this.cum_distance[i_hint+1]) ) {
				// If that doesn't work, find the segment using binary search.
				i_hint = binary_search( this.cum_distance, d );
				if( this.cum_distance[i_hint] > d )
					--i_hint;
			}
		}
		return i_hint;
	}
	
	xy_from_distance( d, i_hint=0 ) {
		d = pos_mod( d, this.cum_distance.last() );
		i_hint = this.i_from_d( d, i_hint );
		
		// Compute the x,y position along the segment.
		const s = this.segment( i_hint );
		const k = (d - this.cum_distance[i_hint]) / (this.cum_distance[i_hint+1] - this.cum_distance[i_hint]);
		const x = s[0][0] + k * (s[1][0] - s[0][0]);
		const y = s[0][1] + k * (s[1][1] - s[0][1]);
		
		return [x, y, i_hint];
	}
		
	xy_from_normal( n, i_hint=0 ) {
		if( n < 1.0 && this.first_lap_distance && this.first_lap_distance != this.lap_distance ) {
			// Adjust for the first lap distance by using the ratio from the end of the lap.
			n = 1.0 - n * this.first_lap_distance / this.lap_distance;
		}
		return this.xy_from_distance( n * this.cum_distance.last(), i_hint );
	}
	
	f_segment_from_normal( n, i_hint ) {
		// Return the segment and the fraction along the segment from the lap normal.
		if( n < 1.0 && this.first_lap_distance && this.first_lap_distance != this.lap_distance ) {
			// Adjust for the first lap distance by using the ratio from the end of the lap.
			n = 1.0 - n * this.first_lap_distance / this.lap_distance;
		}
		const d = (n * this.cum_distance.last()) % this.cum_distance.last();
		i_hint = this.i_from_d( d, i_hint );
		return [i_hint, (d - this.cum_distance[i_hint]) / (this.cum_distance[i_hint+1] - this.cum_distance[i_hint])];
	}
	
	heading_from_normal( n, i_hint=0 ) {
		if( n < 1.0 && this.first_lap_distance && this.first_lap_distance != this.lap_distance ) {
			// Adjust for the first lap distance by using the ratio from the end of the lap.
			n = 1.0 - n * this.first_lap_distance / this.lap_distance;
		}
		i_hint = this.i_from_d( n * this.cum_distance.last(), i_hint );
		return [this.segment_heading( i_hint ), i_hint];
	}
}
	
class Rider {
	constructor( bib, race_times, info, color ) {
		this.bib = bib;
		this.i_lap = 0;						// Cached index of the last current lap.
		this.i_segment = 0;					// Cached index of the last course segment.
		this.color = color ? color : ('rgb(' + Math.trunc(128+128*rnd()) + ',' + Math.trunc(128+128*rnd()) + ',' + Math.trunc(128+128*rnd()) + ')');
		this.info = info ? info : new Map();
		
		this.race_times = race_times;		// Race times per lap (seconds).  Note: race_times[0] is the start offset.
	}
		
	get_lap_normal( t ) {
		// Recall that the first race time is the start offset.
		if( !this.race_times || t <= this.race_times[0] ) {
			this.i_lap = 0;
			return 0.0;							// If before the start, return the beginning of a lap.
		}
		if( t >= this.race_times.last() ) {
			this.i_lap = this.race_times.length;
			return this.race_times.length		// If at the end, return the number of laps.
		}
		
		// Find the race time interval that contains the time.
		try {
			// First, check the current lap index.
			if( this.race_times[this.i_lap] <= t && t < this.race_times[this.i_lap+1] )
				return this.i_lap + (t - this.race_times[this.i_lap]) / (this.race_times[this.i_lap+1] - this.race_times[this.i_lap]);
			
			// Second, check the next lap index.
			this.i_lap += 1
			if( this.race_times[this.i_lap] <= t && t < this.race_times[this.i_lap+1] )
				return this.i_lap + (t - this.race_times[this.i_lap]) / (this.race_times[this.i_lap+1] - this.race_times[this.i_lap]);
		}
		catch( err ) {
			// Catch any index errors.
		}

		// Finally, do binary search.
		this.i_lap = binary_search( this.race_times, t )
		if( this.i_lap == this.race_times.length || this.race_times[this.i_lap] > t )
			--this.i_lap;
		return this.i_lap + (t - this.race_times[this.i_lap]) / (this.race_times[this.i_lap+1] - this.race_times[this.i_lap]);
	}
		
	finished( t ) {
		return t > this.race_times.last();
	}
		
	get_xy( course, t ) {
		const lap_normal = this.get_lap_normal( t );
		// Get the current coordinates of this rider.
		let x, y;
		[x, y, this.i_segment] = course.xy_from_normal( lap_normal, this.i_segment );
		return [x, y];
	}
	
	get_heading( course, t ) {
		const lap_normal = this.get_lap_normal( t );
		// Get the current coordinates of this rider.
		let heading;
		[heading, this.i_segment] = course.heading_from_normal( lap_normal, this.i_segment );
		return heading;
	}
	
	get_initials() {
		let initials = '';
		if( this.info.hasOwnProperty('LastName') )
			initials += this.info.LastName.slice(0,1);
		if( this.info.hasOwnProperty('FirstName') )
			initials += this.info.FirstName.slice(0,1);
		return initials;
	}
	
	get_last_first() {
		let s = [];
		if( this.info.hasOwnProperty('LastName') )
			s.push( this.info.LastName.toUpperCase() );
		if( this.info.hasOwnProperty('FirstName') )
			s.push( this.info.FirstName );
		return s.join(', ');
	}
}

//-----------------------------------------------------------------------

const altigraph_ratio = 0.1;

class TopView {
	constructor( canvas, course, riders, focus_bib=null ) {
		this.canvas = canvas;
		this.course = course;
		this.set_riders( riders );
		if( focus_bib )
			this.set_focus_bib( focus_bib );
		
		this.is_running = false;
		this.t = 0.0;
		this.t_factor = 20.0;
		this.frames_per_second = 30;
		this.dt_animation = null;
		this.zoom = 1.5;
		this.animate = true;
		this.animate_state_cache = true;
		this.focus_rider_cur = null;
		
		// Media and zoom control.
		this.button_rects = [];
		const skip_back = "⏮";
		const play_pause = "⏯";
		const skip_forward = "⏭";
		const speed_up = "⏫︎";
		const speed_down = "⏬︎";	
		const zoom_in = "+🔍";
		const zoom_out = "-🔍";
		
		this.button_handlers = [
			[skip_back,		this.skip_back_animation.bind(this), 1.0],
			[play_pause,	this.play_pause.bind(this), 1.0],
			[skip_forward,	this.skip_forward_animation.bind(this), 1.0],
			[speed_up,		this.speed_up.bind(this), 1.0],
			[speed_down,	this.speed_down.bind(this), 1.0],
			[zoom_in,		this.zoom_in.bind(this), 0.7],
			[zoom_out,		this.zoom_out.bind(this), 0.7]
		].reverse();	// Draw from right to left.
		
		// Focus rider select.
		const focus_up = "▲";
		const focus_down = "▼";
		
		this.focus_button_rects = [];
		this.focus_button_handlers = [
			[focus_up,			this.focus_up.bind(this), 1.0],
			[focus_down,		this.focus_down.bind(this), 1.0]
		].reverse();
		
		// Event handlers.
		canvas.addEventListener( "keydown", this.OnKeyDown.bind(this), true );
		canvas.addEventListener( "wheel", this.OnMouseWheel.bind(this), false );
		
		this.ev_cache = [];
		canvas.addEventListener( "pointerdown", this.OnPointerDown.bind(this), false );
		canvas.addEventListener( "pointermove", this.OnPointerMove.bind(this), false );
		canvas.addEventListener( "pointerleave", this.OnPointerLeave.bind(this), false );
		canvas.addEventListener( "pointerup", this.OnPointerUp.bind(this), false );
		
		document.addEventListener( "visibilitychange", this.OnVisibilityChange.bind(this), false );
	}
	
	set_t_factor_zoom() {
		// Guess a good t_factor and zoom based on the race data.
		if( this.is_running ) {
			this.t_factor = 1.0;
			return;
		}
		if( this.riders.length === 0 )
			return;
		
		let r_best = [this.riders[0], -this.riders[0].race_times.length, this.riders[0].race_times.last()];
		for( let r of this.riders ) {
			let r_cur = [r, -r.race_times.length, r.race_times.last()];
			let d = 0;
			for( let i = 1; i < 3 && d == 0; ++i )
				d = r_cur[i] - r_best[i];
			if( d < 0 )
				r_best = r_cur;
		}
		// Pick a time factor so we get a minute per lap.
		let r_winner = r_best[0];
		let best_laps, best_time;
		if( r_winner.race_times.length === 2 ) {
			best_laps = 1;
			best_time = r_winner.race_times[1] - r_winner.race_times[0];
		}
		else {
			best_laps = r_winner.race_times.length - 2;
			best_time = r_winner.race_times.last() - r_winner.race_times[1];
		}
		const lap_time_target = 60.0;	// Target of one minute per lap.
		const lap_time = best_time / best_laps;
		this.t_factor = Math.round( 2.0 * lap_time / lap_time_target ) / 2.0;
		this.change_t_factor( 0 );
	}
	
	OnResize( event ) {
		this.canvas.width = window.innerWidth;
		this.canvas.height = window.innerHeight;
		this.draw();
	}

	OnMouseWheel( event ) {
		const r = event.deltaY;
		if( event.shiftKey )
			this.change_zoom( -r );
		else
			this.change_t_factor( -r );
	}
	
	OnPointerDown( event ) {
	    const rect = this.canvas.getBoundingClientRect();
		const x = event.clientX - rect.left;
		const y = event.clientY - rect.top;
		
		// Check if this event is on a button.
		for( let [x1, y1, x2, y2, text, handler, ...rest] of this.button_rects ) {
			if( x1 <= x && x < x2 && y1 <= y && y < y2 ) {
				handler();
				return;
			}
		}
		// Add the event to the list.
		this.ev_cache.push( event );
	}
	
	OnPointerLeave( event ) {
		// Reset the event cache when the pointer leaves.
		this.ev_cache = [];
	}
	
	OnPointerMove( event ) {
		if( this.ev_cache.length === 0 )
			return;
		
		function event_replace( ev_cache, event ) {
			const index = ev_cache.findIndex( (e) => e.pointerId === event.pointerId );
			if( index >= 0 )
				ev_cache[index] = event;		
		}
		
		if( this.ev_cache.length === 1 ) {
			/*
			// Change the speed based on the change of y.
			const y_cur = this.ev_cache[0].clientY;
			event_replace( this.ev_cache, event );
			const y_new = this.ev_cache[0].clientY;
			this.change_t_factor( y_new - y_cur );
			*/
		}
		else if( this.ev_cache.length === 2 ) {
			// Pinch zoom.
			const delta_cur = Math.abs( this.ev_cache[1].clientX - this.ev_cache[0].clientX );
			event_replace( this.ev_cache, event );
			const delta_new = Math.abs( this.ev_cache[1].clientX - this.ev_cache[0].clientX );
			this.change_zoom( delta_new - delta_cur );
		}
	}
	
	OnPointerUp( event ) {
		// Remove the event from the cache.
		const index = this.ev_cache.findIndex( (ev) => ev.pointerId === ev.pointerId );
		if( index >= 0 )
			this.ev_cache.splice(index, 1);
	}
	
	OnVisibilityChange( event ) {
		// Turn the animation on/off depending on the visibiity of the tab.
		if( document.visibilityState === "visible" ) {
			this.animate = this.animate_state_cache;
			if( this.animate )
				this.start_animation();
		}
		else {
			this.animate_state_cache = this.animate;
			this.stop_animation();
		}
	}
			
	OnKeyDown( event ) {
		console.log( 'called' );
		switch( event.key ) {
			case "+":
				if( event.ctrlKey || event.metaKey )
					this.change_zoom( 1 );
				break;
			case "-":
				if( event.ctrlKey || event.metaKey )
					this.change_zoom( -1 );
				break;
			case "ArrowUp":
				this.change_zoom( 1 );
				break;
			case "ArrowDown":
				this.change_zoom( -1 );
				break;
			case "ArrowLeft":
				this.change_t_factor( -1 );
				break;
			case "ArrowRight":
				this.change_t_factor( 1 );
				break;
		}
	}

	set_riders( riders ) {
		this.riders = riders;
		this.r_xyn = this.riders.map( (r) => [r, 0.0, 0.0, 0.0] );
		this.focus_rider = null;
		this.max_laps = 1;
		for( let r of riders )
			this.max_laps = Math.max( this.max_laps, r.race_times.length-1 );
		
		let collator = new Intl.Collator();
		this.sorted_riders = this.riders.map( (r) => r );
		this.sorted_riders.sort( function(a, b) {
				return collator.compare( a.get_last_first(), b.get_last_first() );
			}
		);
		this.sorted_riders.unshift( null );
		this.i_focus_rider = 0;
	}
	
	set_focus_bib( bib ) {
		this.i_sorted = 0;
		for( let i = 1; i < this.sorted_riders.length; ++i ) {
			if( this.sorted_riders[i].bib == bib ) {
				this.i_sorted = 0;
				break;
			}
		}
	}
		
	set_t( t=0.0 ) { this.t = t; }

	rewind_animation() {
		this.t = 0.0;
		this.dt_animation = new Date();
		this.start_animation();
	}
		
	start_animation() {
		this.dt_animation = new Date();
		this.animate = true;
		setTimeout( () => this.OnTimer(), 1000.0 / this.frames_per_second );
	}
		
	stop_animation() { this.animate = false; }
	
	play_pause() {
		if( this.animate )
			this.stop_animation();
		else
			this.start_animation();
	}
	
	speed_up() { this.change_t_factor(1); }
	speed_down() { this.change_t_factor(-1); }
	
	zoom_in() { this.change_zoom(1); }
	zoom_out() { this.change_zoom(-1); }

	skip_back_animation() {
		if( this.focus_rider_cur === null || this.focus_rider_cur.race_times.length < 2 )
			return;
		const n_prev = Math.min( this.focus_rider_cur.race_times.length-2, Math.max( 0, Math.trunc(this.focus_rider_cur.get_lap_normal( this.t )) - 1 ));
		this.set_t( this.focus_rider_cur.race_times[n_prev] );
		this.draw();
	}
	
	skip_forward_animation() {
		if( this.focus_rider_cur === null || this.focus_rider_cur.race_times.length < 2 )
			return;
		const n_next = Math.min( this.focus_rider_cur.race_times.length-1, Math.trunc(this.focus_rider_cur.get_lap_normal(this.t)) + 1 );
		this.set_t( this.focus_rider_cur.race_times[n_next] );
		this.draw();
	}
	
	focus_up() {
		if( this.sorted_riders && this.sorted_riders.length ) {
			this.i_focus_rider = (this.i_focus_rider + this.sorted_riders.length-1) % this.sorted_riders.length;
			this.focus_rider = this.sorted_riders[this.i_focus_rider];
		}
	}
	focus_down() {
		if( this.sorted_riders && this.sorted_riders.length ) {
			this.i_focus_rider = (this.i_focus_rider + 1) % this.sorted_riders.length;
			this.focus_rider = this.sorted_riders[this.i_focus_rider];
		}
	}
		
	OnTimer() {
		const dt = new Date();
		this.t += (dt.getTime() - this.dt_animation.getTime()) / 1000.0 * this.t_factor;
		this.dt_animation = dt;
		this.draw();
		if( this.animate ) {
			// Try to draw frames on a consistent interval.
			const millis_for_draw = (new Date()).getTime() - dt.getTime();
			const millis_for_frame = 1000.0 / this.frames_per_second;
			setTimeout( () => this.OnTimer(), Math.max(1, millis_for_frame - millis_for_draw) );
		}
	}
		
	change_zoom( z ) {
		const zoom_last = this.zoom;
		this.zoom += Math.sign(z) * 0.2;
		this.zoom = Math.max( 0.5, Math.min(8.0, this.zoom) );
		if( zoom_last != this.zoom )
			this.draw();
	}

	change_t_factor( tf ) {
		const t_factor_last = this.t_factor;
		this.t_factor += Math.sign( tf ) * 0.5;
		this.t_factor = Math.max( 1.0, Math.min(40.0, this.t_factor) );
		if( t_factor_last != this.t_factor )
			this.draw();
	}
		
	draw_altigraph( gc, focus_rider ) {
		if( !this.course.altigraph )
			return;

		const elevation_min = this.course.elevation_min;
		const elevation_delta = this.course.elevation_max - elevation_min;
		if( elevation_delta === 0 )
			return;

		const [p_width, p_height] = [this.canvas.width, this.canvas.height];

		gc.save();

		// Transform everything so it shows up properly on the screen.
		let [p_altigraph_width, p_altigraph_height] = [p_width, p_height * altigraph_ratio];
		gc.translate( p_width - p_altigraph_width, p_height - p_altigraph_height );	// Move to the top left of the altigraph.
		const x_scale = p_altigraph_width / this.course.altigraph.last()[0];
		const y_scale = p_altigraph_height / elevation_delta / x_scale;
		gc.scale( x_scale, x_scale );												// Scale the height and width to fit.

		// Draw a sky.
		gc.fillStyle = "rgb(135, 206, 235)";
		gc.fillRect( 0.0, 0.0, p_altigraph_width/x_scale, p_altigraph_height/x_scale*y_scale );

		// Draw the altgraph shape.
		gc.beginPath()
		gc.moveTo( 0.0, y_scale*elevation_delta );
		let d_last = -100;
		for( let [d, e, g] of this.course.altigraph ) {
			if( d - d_last < 20 )
				continue;
			d_last = d;
			e = elevation_delta - (e - elevation_min);
			gc.lineTo( d, y_scale * e );
		}
		gc.lineTo( this.course.altigraph.last()[0], y_scale*elevation_delta );
		gc.closePath();
		
		gc.fillStyle = "rgb(0, 0, 0)";
		gc.fill();
		
		// Draw the max delta elevation.
		let s = `Δ ${elevation_delta.toFixed(1)}m`;
		gc.textBaseline = "top";
		gc.font = (12/x_scale) + "px Arial";
		gc.fillStyle = "rgb(54,54,54)";
		gc.fillText( s, 0, 0 );
				
		// Draw the position of the focus rider.
		if( focus_rider ) {
			let [i, fraction] = this.course.f_segment_from_normal( focus_rider.get_lap_normal(this.t), focus_rider.i_segment );
			focus_rider.i_segment = i;
			if( i < this.course.altigraph.length - 1 ) {
				let d = this.course.altigraph[i][0] + (this.course.altigraph[i+1][0] - this.course.altigraph[i][0]) * fraction;
				let e = this.course.altigraph[i][1] + (this.course.altigraph[i+1][1] - this.course.altigraph[i][1]) * fraction;
				e = elevation_delta - (e - elevation_min);
				
				const [x, y] = [d , y_scale * e];

				gc.strokeStyle = "rgb(255,140,0)";
				gc.lineWidth = 3/x_scale;
				gc.beginPath();
				gc.moveTo( x, 0 );
				gc.lineTo( x, elevation_delta * y_scale );
				gc.stroke();

				const radius = 10;
				
				const x_gradient = x-radius/x_scale/2.0;
				const y_gradient = y-radius/x_scale/2.0;
				let gradient = gc.createRadialGradient(
					x_gradient, y_gradient, 0.0,
					x_gradient, y_gradient, radius / 0.8 * 2.0 / x_scale
				);
				gradient.addColorStop( 0.0, focus_rider.color );
				gradient.addColorStop( 1.0, "black" );
				gc.fillStyle = gradient;
				gc.beginPath();
				gc.ellipse( x, y, radius/x_scale, radius/x_scale, 0.0, 0.0, Math.PI*2.0 );
				gc.fill();
			}
		}
		gc.restore();
	}
	
	draw_buttons( gc ) {
		const [p_width, p_height] = [this.canvas.width, this.canvas.height];
		
		// Array of buttons with bounding rectangles and handlers.
		this.button_rects = [];

		gc.save();
		
		let t_height = 30*1.33333;
		gc.font = t_height + "px Arial";
		gc.textBaseline = "top";
		const space_width = gc.measureText(" ").width;
		const button_height = t_height * 1.15;
		const lineWidth = 3;

		// Media and zoom control.
		let x_button = p_width, y_button = 0
		for( let [text, handler, factor] of this.button_handlers ) {
			gc.font = (t_height * factor) + "px Arial";
			const t_width = gc.measureText(text).width + space_width;
			const button_width = t_width + space_width;
			x_button -= t_width + space_width;
			this.button_rects.push( [x_button, y_button, x_button + button_width, y_button + button_height, text, handler, factor] );
			
			// If the race is running, just show the zoom buttons.
			if( this.button_rects.length == 2 && this.is_running )
				break;
		}

		this.button_rects.reverse();
		let [x0, y0] = [this.button_rects[0][0], this.button_rects[0][1]];
		let [x1, y1] = [x0, this.button_rects[0][3]];
		let gradient = gc.createLinearGradient( x0, y0, x1, y1);
		gradient.addColorStop( 0.0, 'rgb(96,96,96)' );
		gradient.addColorStop( 0.5, 'rgb(200,200,200)' );
		gradient.addColorStop( 1.0, 'rgb(96,96,96)' );
		gc.lineWidth = lineWidth;
		let i = 0;
		for( let [x1, y1, x2, y2, text, handler, factor] of this.button_rects ) {
			const r = [x1, y1, x2-x1, y2-y1];
			gc.strokeStyle = "black";
			gc.fillStyle = gradient;
			gc.strokeRect( ...r );
			gc.fillRect( ...r );

			gc.font = (t_height * factor) + "px Arial";
			const t_width = gc.measureText(text).width;
			const x_text = x1 + ((x2-x1) - t_width) / 2;
			const y_text = y1 + ((y2-y1) - (t_height * factor)) / 2;
			gc.fillStyle = "black";
			gc.fillText( text, x_text, y_text );
		}
		
		//--------------------------------------------------------------
		// Focus selection.
		//
		x_button = p_width;
		y_button = button_height + lineWidth/2;
		this.focus_button_rects = [];
		for( let [text, handler, factor] of this.focus_button_handlers ) {
			gc.font = (t_height * factor) + "px Arial";
			const t_width = gc.measureText(text).width + space_width;
			const button_width = t_width + space_width;
			x_button -= t_width + space_width;
			this.focus_button_rects.push( [x_button, y_button, x_button + button_width, y_button + button_height, text, handler, factor] );
		}

		this.focus_button_rects.reverse();
		[x0, y0] = [this.focus_button_rects[0][0], this.focus_button_rects[0][1]];
		[x1, y1] = [x0, this.focus_button_rects[0][3]];
		gradient = gc.createLinearGradient( x0, y0, x1, y1);
		gradient.addColorStop( 0.0, 'rgb(96,96,96)' );
		gradient.addColorStop( 0.5, 'rgb(200,200,200)' );
		gradient.addColorStop( 1.0, 'rgb(96,96,96)' );
		gc.lineWidth = lineWidth;
		for( let [x1, y1, x2, y2, text, handler, factor] of this.focus_button_rects ) {
			const r = [x1, y1, x2-x1, y2-y1];
			gc.strokeStyle = "black";
			gc.fillStyle = gradient;
			gc.strokeRect( ...r );
			gc.fillRect( ...r );

			gc.font = (t_height * factor) + "px Arial";
			const t_width = gc.measureText(text).width;
			const x_text = x1 + ((x2-x1) - t_width) / 2;
			const y_text = y1 + ((y2-y1) - (t_height * factor)) / 2;
			gc.fillStyle = "black";
			gc.fillText( text, x_text, y_text );
		}
		const text = " " + (this.i_focus_rider === 0 ? "Leader" : this.sorted_riders[this.i_focus_rider].get_last_first()) + " ";
		const x_text = this.focus_button_rects[0][0];
		const y_text = y0 + (button_height - t_height) / 2;
		gc.textAlign = "right";
		gc.fillText( text, x_text, y_text );
		
		this.button_rects = this.button_rects.concat( this.focus_button_rects );
		
		gc.restore();
	}
	
	draw_info( gc, focus_rider ) {
		if( !this.r_xyn || this.r_xyn.length === 0 )
			return;
			
		const max_laps = this.max_laps;
		
		gc.save();

		const t_height = 16*1.33333;
		gc.font = t_height + "px Arial";
		gc.fillStyle = "black";
		gc.textBaseline = "top";
		
		const n = focus_rider.get_lap_normal( this.t );
		const t_x = t_height, t_y = t_height;
		[
			`Laps to go: ${Math.max(max_laps-n, 0.0).toFixed(2)}/${max_laps}`,
			`Race Time: ${format_t(this.t)}`,
			`Playback Speed: ${this.t_factor.toFixed(1)}x`,
			`Zoom: ${this.zoom.toFixed(1)}x`
		].forEach( (s,i) => gc.fillText( s, t_x, t_y+t_height*1.15*i ) );
		gc.restore();
	}
	
	set_matrix( gc, focus_rider ) {
		const [p_width, p_height] = [this.canvas.width, this.canvas.height * (1.0 - altigraph_ratio)];
		
		if( !focus_rider ) {
			let scale = p_width / this.course.size[0];
			if( this.course.size[1] * scale > p_height )
				scale = p_height / this.course.size[1];
			scale *= 0.9;
			this.scale = scale;
			
			gc.translate( p_width*(1-0.9)/2, p_height );
			gc.scale( scale, scale );
			return;
		}
		
		// Fit the entire course into the window (more or less).
		let scale = p_width / this.course.size[0];
		if( this.course.size[1] * scale > p_height )
			scale = p_height / this.course.size[1];
		scale *= this.zoom;
		this.scale = scale;
		
		// Set 0,0 as the center of the screen.
		gc.translate( p_width/2, p_height/2 );
		// Scale to show the course.
		gc.scale( scale, scale );

		// Center the display on the focus rider.
		gc.translate( ...focus_rider.get_xy(this.course, this.t).map( (v) => -v ) );
	}
	
	draw() {
		const p_width = this.canvas.width, p_height = this.canvas.height;
				
		let gc = this.canvas.getContext("2d");
		gc.save();
		gc.textBaseline = 'top';

		// Set grass green background.
		gc.fillStyle = "rgb(34, 139, 34)";
		gc.fillRect( 0, 0, p_width, p_height );
		
		// Update the positions and lap normals for all riders.
		for( let v of this.r_xyn ) {
			let r = v[0];
			[v[1], v[2]] = r.get_xy( this.course, this.t );
			v[3] = r.get_lap_normal( this.t );
		}
			
		// Sort by lap normal, then by reverse laps completed, then by increasing finish time.
		this.r_xyn.sort( function( a, b ) {
				let ka = [a[3], -a[0].race_times.length, a[0].race_times.last()];
				let kb = [b[3], -b[0].race_times.length, b[0].race_times.last()];
				for( const [va,vb] of zip(ka, kb) ) {
					if( va < vb ) return -1;
					if( vb < va ) return  1;
				}
				return 0;
			}
		);
		
		// If no focus rider, choose the leader.
		let focus_rider = null;
		if( this.r_xyn.length )
			focus_rider = (this.focus_rider !== null ? this.focus_rider : this.r_xyn.last()[0]);
		this.focus_rider_cur = focus_rider;
		
		// Draw the course based on the focus rider.		
		this.set_matrix(gc, focus_rider);

		const shoulder_width = 40.0/this.scale;
		
		// Get a reasonable font.
		const font_size_px = (13*1.33333) / this.scale;

		// Draw the trees and sheep.
		gc.font = (font_size_px * 1.5) + "px Arial";
		this.course.tree_points.forEach( (p, i) => gc.fillText( ["🌲","🌳",][i&1], ...p ) );
		this.course.sheep_points.forEach( (p, i) => gc.fillText( "🐑", ...p ) );

		// Set the main font.
		gc.font = font_size_px + "px Arial";
		
		gc.beginPath();
		gc.moveTo( ...this.course.course_points[0] );
		for( let i = 1; i < this.course.course_points.length; ++i )
			gc.lineTo( ...this.course.course_points[i] );
		if( this.course.is_loop )
			gc.closePath();
		
		// Road shoulder
		gc.lineCap = 'round';
		gc.lineJoin = 'round';
		gc.lineWidth = shoulder_width;
		gc.strokeStyle = "rgb(194,178,128)";			// Sand.
		gc.stroke();
		
		// Pavement.
		gc.lineWidth = shoulder_width*0.8;
		gc.strokeStyle = "rgb(82,77,80)";				// Pavement.
		gc.stroke();
		
		// Center line.
		gc.lineWidth = 3/this.scale;					// Centerline
		gc.strokeStyle = "rgb(196,196,196)";
		gc.stroke();
		
		// Finish line.
		const dx = shoulder_width/2.0 * this.course.finish_dx;
		const dy = shoulder_width/2.0 * this.course.finish_dy;
		const p_finish = this.course.points[0];
		const p_begin = [p_finish[0] - dx, p_finish[1] - dy];
		const p_end   = [p_finish[0] + dx, p_finish[1] + dy];
		
		gc.beginPath();
		gc.moveTo( ...p_begin );
		gc.lineTo( ...p_end );

		// White finish line background.
		gc.lineWidth = shoulder_width/5;
		gc.strokeStyle = "white";
		gc.stroke();
	
		// Black finish line center
		gc.lineWidth = shoulder_width/22;
		gc.strokeStyle = "black";
		gc.stroke();
		
		// Draw two finish flags on either side.
		const fl_text = "🏁";
		gc.textBaseline = "bottom";
		const [x_text, y_text] = [gc.measureText( fl_text ).width, font_size_px];
		gc.fillText( fl_text, p_end[0], p_end[1] )
		gc.fillText( fl_text, p_begin[0], p_begin[1] )
		gc.textBaseline = "top";
		
		// Draw the riders.
		// Draw the balls.
		const radius = shoulder_width*0.8 / 2.0;
		let i_focus_rider = null;
		let i_last_rider = -1;
		
		function draw_rider_ball( r, x, y, scale ) {
			const x_gradient = x-radius/2.0;
			const y_gradient = y-radius/2.0;
			
			let gradient = gc.createRadialGradient(
				x_gradient, y_gradient, 0.0,
				x_gradient, y_gradient, shoulder_width
			);
			gradient.addColorStop( 0.0, r.color );
			gradient.addColorStop( 1.0, "black" );
			gc.fillStyle = gradient;
			gc.beginPath();
			gc.ellipse( x, y, radius, radius, 0.0, 0.0, Math.PI*2.0 );
			gc.fill();
			
			if( r === focus_rider ) {
				gc.lineWidth = 4/scale;
				gc.strokeStyle = "rgb(0,196,196)";
				gc.stroke();
			}
		}
		
		for( let i = 0; i < this.r_xyn.length; ++i ) {
			let [r, x, y, n] = this.r_xyn[i];
			if( r == focus_rider )
				i_focus_rider = i;
				
			if( r.finished(this.t) ) {
				if( i_focus_rider === null ) {
					for( ; i < this.r_xyn.length; ++i ) {
						if( this.r_xyn[i][0] == focus_rider ) {
							i_focus_rider = i;
							break;
						}
					}
				}
				break;
			}
			
			draw_rider_ball( r, x, y, this.scale );
			i_last_rider = i;
		}
		
		if( i_focus_rider !== null ) {
			let [r, x, y, n] = this.r_xyn[i_focus_rider];
			draw_rider_ball( r, x, y, this.scale );
		}
		
		if( i_last_rider < 0 ) {
			this.set_t( 0.0 );
			gc.restore();
			return;
		}
		
		gc.fillStyle = 'white';
			
		// Draw the labels.
		if( i_focus_rider !== null ) {
			const label_max = 10;	// Maximum number of rider labels to draw.
			
			const focus_n = focus_rider.get_lap_normal(this.t);
			let diff_normal = null;
			if( this.course.is_loop ) {
				diff_normal = function( n ) {
					const d = fract( Math.abs(focus_n - n) );
					return Math.min( d, 1-d );
				}
			}
			else {
				diff_normal = function( n ) {
					return Math.abs(focus_n - n);
				}
			}
			
			// Create a new array to sort by riders closest to the focus_rider.
			let r_xy_lap = this.r_xyn.slice(0, i_last_rider + 1);
			
			// Sort the riders by closest on the track.
			r_xy_lap.sort( function( a, b ) {
					let ka = [diff_normal(a[3]), -a[0].race_times.length, a[0].race_times.last()];
					let kb = [diff_normal(b[3]), -b[0].race_times.length, b[0].race_times.last()];
					for( const [va,vb] of zip(ka, kb) ) {
						if( va < vb ) return -1;
						if( vb < va ) return  1;
					}
					return 0;
				}
			);
			
			const t_cur = this.t, scale_cur = this.scale;
			gc.strokeStyle = "rgb(200,200,200)";
			gc.lineWidth = 2/scale_cur;
			function draw_rider_text( r, x, y, go_high=true, do_fill=true ) {
				const y_offset = 20/scale_cur;
				const x_text = x + y_offset*.22, y_text = !go_high ? (y + y_offset) : (y - 2*font_size_px*1.1 - y_offset);
				let y_cur = y_text;
				let text_width_max = 0;
				const text = [r.bib.toString(), r.get_initials()];
				for( const t of text ) {
					text_width_max = Math.max( text_width_max, gc.measureText(t).width );
					if( do_fill )
						gc.fillText( t, x_text, y_cur );
					y_cur += font_size_px * 1.1;
				}
				if( do_fill ) {
					gc.beginPath();
					gc.moveTo( x, y );
					gc.lineTo( x, !go_high ? (y_cur - font_size_px * 0.3) : y_text );
					gc.stroke();
				}
				return [x_text, y_text, x_text+text_width_max, y_cur];
			}
			let text_rect = [];
			if( !this.r_xyn[i_focus_rider][0].finished(this.t) )
				text_rect.push( draw_rider_text(...this.r_xyn[i_focus_rider].slice(0,3), true, true) );
			const i_max = Math.min( r_xy_lap.length, label_max );
			for( let i = +(r_xy_lap[0][0] == this.r_xyn[i_focus_rider][0]); i < i_max; ++i ) {
				// Try to draw the label low and high.
				for( let j = 0; j < 2; ++j ) {
					const tr = draw_rider_text( ...r_xy_lap[i].slice(0,3), j==0, false );
					if( !text_rect.some( (r) => overlaps(r, tr) ) ) {
						text_rect.push( draw_rider_text( ...r_xy_lap[i].slice(0,3), j==0, true) );
						break;
					}
				}
			}
		}
		
		gc.restore();
		if( this.r_xyn.length ) {
			this.draw_info( gc, focus_rider );
			this.draw_buttons( gc );
		}
		this.draw_altigraph( gc, focus_rider );
	}
}

function gaussian( mean, stdev ) {
	let y2;
	let use_last = false;
	return function() {
		let y1;
		if (use_last) {
			y1 = y2;
			use_last = false;
		}
		else {
			let x1, x2, w;
			do {
				x1 = 2.0 * Math.random() - 1.0;
				x2 = 2.0 * Math.random() - 1.0;
				w = x1 * x1 + x2 * x2;
			} while (w >= 1.0);
			w = Math.sqrt((-2.0 * Math.log(w)) / w);
			y1 = x1 * w;
			y2 = x2 * w;
			use_last = true;
		}

		const retval = mean + stdev * y1;
		if (retval > 0)
			return retval;
		return -retval;
	}
}

function random_letter() {
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
	return characters.charAt( Math.random()*characters.length );
}

function create_riders( course, laps_max = 6 ) {
	const d = course.adjusted_distance();
	let speed = gaussian( 46.0, 4.0 );
	let riders = [];
	let winning_time = +Infinity;
	for( let i = 0; i < 40; ++i ) {
		let race_times = [0.0];
		for( let lap = 0; lap < laps_max; ++lap )
			race_times.push( race_times.last() + d / speed() );
		riders.push( new Rider(i+100, race_times, {FirstName:random_letter(), LastName:random_letter()}) );

		if( race_times.last() < winning_time )
			winning_time = race_times.last();
	}
	// Make sure all riders finish after the leader.
	for( let r of riders ) {
		while( r.race_times[r.race_times.length-2] > winning_time )
			r.race_times.pop();
	}
	return riders;
}

/*

var top_view = null;
function onBodyLoad() {
	let canvas = document.getElementById('id_canvas');
	let course = new Course( lat_lon_elevation, true );
	let riders = create_riders( course );

	top_view = new TopView( canvas, course, riders );
	top_view.set_t_factor_zoom();
	
	window.addEventListener( "resize", top_view.OnResize.bind(top_view) );
	top_view.OnResize();
	top_view.start_animation();
}

'''
</script>

<style>
body { margin: 0; } 
canvas { display: block; } 
</style>

</head>
<body onload="onBodyLoad();">
	<canvas id="id_canvas"></canvas>
</body>
</html>
'''

*/
