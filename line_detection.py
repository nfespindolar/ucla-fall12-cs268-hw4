#!/usr/bin/python

'''
Copyright (c) 2012 Viet Nguyen

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify, merge,
publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
'''

import math
import random
import sys

import cv2
import numpy as np

import intrinsic_calibration

class LineOfInterest():
	'''
	TODO DOCUMENTATION
	'''

	def __init__(self, left_point, width):
		'''
		TODO DOCUMENTATION
		'''
		self.left_point = left_point
		self.width = width
		self.right_point = (self.left_point[0]+width, self.left_point[1])
	
	def __str__(self):
		return str(self.left_point)+', '+self.width

def define_lines_of_interest():
	'''
	TODO DOCUMENTATION
	'''
	img_region = (0, 0, 640, 480)
	vertical_interval = (218, 368)
	vertical_range = vertical_interval[1]-vertical_interval[0]
	vertical_step = 10
	width_interval = (36, 120)
	width_range = width_interval[1]-width_interval[0]
	left_center_interval = (205, -15)
	left_center_range = left_center_interval[1]-left_center_interval[0]
	right_center_interval = (280, 440)
	right_center_range = right_center_interval[1]-right_center_interval[0]

	left_lines_of_interest = []
	right_lines_of_interest = []

	for y in range(vertical_interval[0], vertical_interval[1]+vertical_step, vertical_step):
		width = int(width_range*(y-vertical_interval[0])/vertical_range)+width_interval[0]
		left_center = int(left_center_range*(y-vertical_interval[0])/vertical_range)+left_center_interval[0]
		right_center = int(right_center_range*(y-vertical_interval[0])/vertical_range)+right_center_interval[0]
		

		left_line = ((left_center-width, y), (left_center+width, y))
		left_line = cv2.clipLine(img_region, left_line[0], left_line[1])[1:] # assumes lines always overlap image region, otherwise the function returns False and the original lines
		left_lines_of_interest.append(LineOfInterest(left_line[0], left_line[1][0]-left_line[0][0]))

		right_line = ((right_center-width, y), (right_center+width, y))
		right_line = cv2.clipLine(img_region, right_line[0], right_line[1])[1:] # assumes lines always overlap image region, otherwise the function returns False and the original lines
		right_lines_of_interest.append(LineOfInterest(right_line[0], right_line[1][0]-right_line[0][0]))
	
	return left_lines_of_interest, right_lines_of_interest

def find_lane_points(canny_image, lines_of_interest, lane):
	'''
	TODO DOCUMENTATION
	'''

	assert(lane == 'left' or lane == 'right')

	if lane == 'left':
		direction = -1
		start_point_name = 'right_point'
		end_point_name = 'left_point'
	elif lane == 'right':
		direction = 1
		start_point_name = 'left_point'
		end_point_name = 'right_point'
	
	lane_points = []

	for line_of_interest in lines_of_interest:
		start_point = getattr(line_of_interest, start_point_name)
		end_point = getattr(line_of_interest, end_point_name)

		x, y = start_point

		while( x * direction <= end_point[0] * direction ):
			intensity_at_point = canny_image[y][x]
			if intensity_at_point == 255:
				lane_points.append((x, y))
				break
			x += direction

	return lane_points

def find_line(points):
	'''
	TODO DOCUMENTATION
	'''

	num_of_iterations = 100
	tolerance = 4.0 # pixels

	bag_of_points = [np.matrix([[x, y]]).T for x, y in points]

	best_line_score = 0
	best_line = None

	iteration_count = 0
	while iteration_count < num_of_iterations:
		
		# select two random points
		random.shuffle(bag_of_points)
		point_a = bag_of_points[0]
		point_b = bag_of_points[1]

		# define the line
		origin = point_a
		unit_dir = (point_b - point_a)
		unit_dir = unit_dir / np.linalg.norm(unit_dir)

		# score this line
		score = 0
		for point in bag_of_points[2:]:
			origin_to_point = point - origin
			proj_on_line = unit_dir * np.vdot(unit_dir.A, origin_to_point.A)
			line_to_point = origin_to_point - proj_on_line
			dist_from_line_to_point = np.linalg.norm(line_to_point)
			if dist_from_line_to_point <= tolerance:
				score += (tolerance - dist_from_line_to_point)

		# compare this to the best line so far
		if score > best_line_score:
			best_line = (origin, unit_dir)
			best_line_score = score

		iteration_count += 1
	
	return best_line

if __name__ == '__main__':

	image_paths = ['LDWS_test/LDWS_test_data {0:03}.bmp'.format(x) for x in range(1, 609)]

	# commented out for now since it isn't being used yet.
	#intrinsic_matrix, distortion_coefficients = intrinsic_calibration.hw4_calibration(False)

	left_lines_of_interest, right_lines_of_interest = define_lines_of_interest()

	cv2.namedWindow('edges')

	#image_paths = image_paths[0:1]
	#image_paths = ['LDWS_test/LDWS_test_data 155.bmp']

	for image_path in image_paths:
		cv_image = cv2.imread(image_path)

		low_threshold = 100
		ratio = 3

		canny_image = cv2.Canny(cv_image, low_threshold, low_threshold*ratio)

		left_lane_points = find_lane_points(canny_image, left_lines_of_interest, 'left')
		right_lane_points = find_lane_points(canny_image, right_lines_of_interest, 'right')
		
		#display_image = cv2.cvtColor(canny_image, cv2.COLOR_GRAY2BGR)
		display_image = cv_image

		for line_of_interest in left_lines_of_interest:
			cv2.line(display_image, line_of_interest.left_point, line_of_interest.right_point, (0, 0, 255), 1, cv2.CV_AA)

		for line_of_interest in right_lines_of_interest:
			cv2.line(display_image, line_of_interest.left_point, line_of_interest.right_point, (255, 0, 0), 1, cv2.CV_AA)

		for point in left_lane_points + right_lane_points:
			cv2.circle(display_image, point, 5, (0, 255, 0))

		img_region = (0, 0, 640, 480)
		colvec_to_tuple = lambda x: (x[0][0], x[1][0])

		left_lane_line = find_line(left_lane_points)
		right_lane_line = find_line(right_lane_points)

		assert(left_lane_line != None)
		assert(right_lane_line != None)

		def draw_line_def(image, img_region, line, color):
			origin, unit_dir = line
			over_line = (colvec_to_tuple(origin+unit_dir*640.0), colvec_to_tuple(origin-unit_dir*640.0))
			over_line = cv2.clipLine(img_region, over_line[0], over_line[1])[1:]
			cv2.line(image, over_line[0], over_line[1], color, 1, cv2.CV_AA)
		
		draw_line_def(display_image, (0, 0, 640, 480), left_lane_line, (255, 0, 255))
		draw_line_def(display_image, (0, 0, 640, 480), right_lane_line, (255, 0, 255))

		cv2.imshow('edges', display_image)
		cv2.waitKey(1)

	# end in an interactive shell so we can look at the values
	try:
		import IPython
		IPython.embed()
	except Exception as e:
		sys.exit()

