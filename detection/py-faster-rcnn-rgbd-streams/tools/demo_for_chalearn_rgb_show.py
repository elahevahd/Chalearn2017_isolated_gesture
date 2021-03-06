#!/usr/bin/env python

# --------------------------------------------------------
# Faster R-CNN
# Copyright (c) 2015 Microsoft
# Licensed under The MIT License [see LICENSE for details]
# Written by Ross Girshick
# --------------------------------------------------------

"""
Demo script showing detections in sample images.

See README.md for installation instructions before running.
"""

import _init_paths
from fast_rcnn.config import cfg
from fast_rcnn.test import im_detect
from fast_rcnn.nms_wrapper import nms
from utils.timer import Timer
import matplotlib.pyplot as plt
import numpy as np
import scipy.io as sio
import caffe, os, sys, cv2
import argparse

CLASSES = ('__background__','hand')

NETS = {'vgg16': ('VGG16',
                  'VGG16_faster_rcnn_final.caffemodel'),
	'vgg16_rgbd_streams_hand': ('VGG16',
                  'vgg16_faster_rcnn_rgbd_streams.caffemodel'),
        'zf': ('ZF',
                  'ZF_faster_rcnn_final.caffemodel'),
	'zf_hand': ('ZF',
		  'zf_faster_rcnn_iter_100000_chalearn_trainval_all.caffemodel')}


def vis_detections(im, class_name, dets, thresh=0.5):
    """Draw detected bounding boxes."""
    inds = np.where(dets[:, -1] >= thresh)[0]
    print inds
    if len(inds) == 0:
        return

    im = im[:, :, (2, 1, 0)]
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.imshow(im, aspect='equal')
    for i in inds:
        bbox = dets[i, :4]
        score = dets[i, -1]

        ax.add_patch(
            plt.Rectangle((bbox[0], bbox[1]),
                          bbox[2] - bbox[0],
                          bbox[3] - bbox[1], fill=False,
                          edgecolor='red', linewidth=3.5)
            )
        ax.text(bbox[0], bbox[1] - 2,
                '{:s} {:.3f}'.format(class_name, score),
                bbox=dict(facecolor='blue', alpha=0.5),
                fontsize=14, color='white')

    ax.set_title(('{} detections with '
                  'p({} | box) >= {:.1f}').format(class_name, class_name,
                                                  thresh),
                  fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    plt.draw()

def demo(net, image_name):
    """Detect object classes in an image using pre-computed object proposals."""

    # Load the demo image
    im_file = os.path.join(cfg.DATA_DIR, 'demo', image_name)
    im = cv2.imread(im_file)

    # Detect all object classes and regress object bounds
    timer = Timer()
    timer.tic()
    scores, boxes = im_detect(net, im)
    timer.toc()
    print ('Detection took {:.3f}s for '
           '{:d} object proposals').format(timer.total_time, boxes.shape[0])

    # Visualize detections for each class
    CONF_THRESH = 0.8
    NMS_THRESH = 0.3
    for cls_ind, cls in enumerate(CLASSES[1:]):
        cls_ind += 1 # because we skipped background
        cls_boxes = boxes[:, 4*cls_ind:4*(cls_ind + 1)]
        cls_scores = scores[:, cls_ind]
        dets = np.hstack((cls_boxes,
                          cls_scores[:, np.newaxis])).astype(np.float32)
        keep = nms(dets, NMS_THRESH)
        dets = dets[keep, :]
	#print dets
        vis_detections(im, cls, dets, thresh=CONF_THRESH)

def demo_chalearn(net, rgb, depth, txt, count):

    im = rgb

    im_depth = depth

     # Detect all object classes and regress object bounds
    timer = Timer()
    timer.tic()
    scores, boxes = im_detect(net, im, im_depth)
    timer.toc()
    print ('Detection took {:.3f}s for '
           '{:d} object proposals').format(timer.total_time, boxes.shape[0])

    # Visualize detections for each class
    CONF_THRESH = 0.8
    NMS_THRESH = 0.3
    for cls_ind, cls in enumerate(CLASSES[1:]):
        cls_ind += 1 # because we skipped background
        cls_boxes = boxes[:, 4*cls_ind:4*(cls_ind + 1)]
        cls_scores = scores[:, cls_ind]
        dets = np.hstack((cls_boxes,
                          cls_scores[:, np.newaxis])).astype(np.float32)
        keep = nms(dets, NMS_THRESH)
        dets = dets[keep, :]
        inds = np.where(dets[:, -1] >= CONF_THRESH)[0]
        if len(inds) == 0:  # No hand > thresh
            return
        inds = inds[:2]
        frameID = '%04d'%count
        txt.write(frameID)
        for i in inds:
            bbox = dets[i, :4]
            for j in range(bbox.shape[0]):
                pos = '%03d'%round(bbox[j])
                txt.write(' ')
                txt.write(pos)
        txt.write('\n')

def demo_chalearn_show(net, rgb, depth, output_video):

    im = rgb

    im_depth = depth

     # Detect all object classes and regress object bounds
    timer = Timer()
    timer.tic()
    scores, boxes = im_detect(net, im, im_depth)
    timer.toc()
    print ('Detection took {:.3f}s for '
           '{:d} object proposals').format(timer.total_time, boxes.shape[0])

    # Visualize detections for each class
    CONF_THRESH = 0.8
    NMS_THRESH = 0.3
    for cls_ind, cls in enumerate(CLASSES[1:]):
        cls_ind += 1 # because we skipped background
        cls_boxes = boxes[:, 4*cls_ind:4*(cls_ind + 1)]
        cls_scores = scores[:, cls_ind]
        dets = np.hstack((cls_boxes,
                          cls_scores[:, np.newaxis])).astype(np.float32)
        keep = nms(dets, NMS_THRESH)
        dets = dets[keep, :]
        inds = np.where(dets[:, -1] >= CONF_THRESH)[0]
	if len(inds) == 0:  # No hand > thresh
            cv2.imshow('show', im)
            cv2.waitKey(2)
            output_video.write(im)
            return
        inds = inds[:2]
        for i in inds:
            bbox = dets[i, :4]
            tlx = int(bbox[0])
            tly = int(bbox[1])
            brx = int(bbox[2])
            bry = int(bbox[3])
            cv2.rectangle(im, (tlx, tly), (brx, bry), (0,0,255), 3)
        cv2.imshow('show', im)
        cv2.waitKey(2)
        output_video.write(im)


def parse_args():
    """Parse input arguments."""
    parser = argparse.ArgumentParser(description='Faster R-CNN demo')
    parser.add_argument('--gpu', dest='gpu_id', help='GPU device id to use [0]',
                        default=0, type=int)
    parser.add_argument('--cpu', dest='cpu_mode',
                        help='Use CPU mode (overrides --gpu)',
                        action='store_true')
    parser.add_argument('--net', dest='demo_net', help='Network to use [vgg16_rgbd_streams_hand]',
                        choices=NETS.keys(), default='vgg16_rgbd_streams_hand')

    args = parser.parse_args()

    return args

if __name__ == '__main__':
    cfg.TEST.HAS_RPN = True  # Use RPN for proposals

    args = parse_args()

    prototxt = os.path.join(cfg.MODELS_DIR, NETS[args.demo_net][0],
                            'faster_rcnn_end2end', 'rgbd_streams/test.prototxt')

    caffemodel = os.path.join(cfg.DATA_DIR, 'faster_rcnn_models',
                              NETS[args.demo_net][1])

    if not os.path.isfile(caffemodel):
        raise IOError(('{:s} not found.\nDid you run ./data/script/'
                       'fetch_faster_rcnn_models.sh?').format(caffemodel))

    if args.cpu_mode:
        caffe.set_mode_cpu()
    else:
        caffe.set_mode_gpu()
        caffe.set_device(args.gpu_id)
        cfg.GPU_ID = args.gpu_id
    net = caffe.Net(prototxt, caffemodel, caffe.TEST)

    print '\n\nLoaded network {:s}'.format(caffemodel)
    # Warmup on a dummy image
    im = 128 * np.ones((300, 500, 3), dtype=np.uint8)
    for i in xrange(2):
        _, _= im_detect(net, im, im)

    # Get imgs from video and detect
    print '\nThis is a demo for hand detection using two-stream faster r-cnn:\n'
    path = os.path.abspath(os.path.join(os.path.abspath(__file__), os.pardir, os.pardir))
    root_path = os.path.join(path, 'ChaLearn2017', 'sample')
    root_save_path = os.path.join(path, 'ChaLearn2017', 'sample')
    rgb_video_name = 'M_00001.avi'
    index = len(rgb_video_name)-4
    depth_video_name = 'K_'+rgb_video_name[2:index]+'.avi'
    print rgb_video_name, depth_video_name, '\n'
    # capture
    output_video_path = root_save_path + '/' + rgb_video_name[0:index] + '_detect.avi'
    output_video = cv2.VideoWriter()
    output_video.open(output_video_path, cv2.cv.CV_FOURCC('M','J','P',"G"), 10, (320, 240), True)
    rgb_capture = cv2.VideoCapture(os.path.join(root_path, rgb_video_name))
    depth_capture = cv2.VideoCapture(os.path.join(root_path, depth_video_name))
    rgb_success, rgb_frame = rgb_capture.read()
    depth_success, depth_frame = depth_capture.read()
    count = 0
    while rgb_success and depth_success:
        # detect the hand in the frame and save the result
        demo_chalearn_show(net, rgb_frame, depth_frame, output_video)
        count+=1
        rgb_success, rgb_frame = rgb_capture.read()
        depth_success, depth_frame = depth_capture.read()
    output_video.release()
    rgb_capture.release()
    depth_capture.release()
    print '---------------------------\n'
                            

