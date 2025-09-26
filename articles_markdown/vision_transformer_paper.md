# An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale

## Authors
- Alexey Dosovitskiy
- Lucas Beyer
- Alexander Kolesnikov
- Dirk Weissenborn
- Xiaohua Zhai
- Thomas Unterthiner
- Mostafa Dehghani
- Matthias Minderer
- Georg Heigold
- Sylvain Gelly
- Jakob Uszkoreit
- Neil Houlsby

## Metadata
- **arXiv ID**: 2010.11929
- **Submitted**: 22 Oct 2020
- **Last Revised**: 3 Jun 2021
- **Subjects**: Computer Vision and Pattern Recognition (cs.CV), Artificial Intelligence (cs.AI), Machine Learning (cs.LG)
- **Source**: https://arxiv.org/abs/2010.11929

## Abstract

While the Transformer architecture has become the de-facto standard for natural language processing tasks, its applications to computer vision remain limited. In vision, attention is either applied in conjunction with convolutional networks, or used to replace certain components of convolutional networks while keeping their overall structure in place.

The authors demonstrate that a pure transformer applied directly to image patches can perform excellently on image classification tasks, achieving state-of-the-art results with fewer computational resources.

## Key Innovations

- **Pure Transformer for Vision**: First successful application of a pure transformer architecture to computer vision without convolutions
- **Image Patch Tokenization**: Treats 16x16 image patches as tokens, similar to words in NLP
- **Scalable Architecture**: Demonstrates excellent scaling properties with model size and data
- **Transfer Learning**: Shows superior performance when pre-trained on large datasets and fine-tuned on smaller ones

## Technical Approach

- **Patch Embedding**: Divides images into fixed-size patches (16x16) and linearly embeds them
- **Position Encoding**: Adds learnable position embeddings to patch embeddings
- **Standard Transformer**: Uses the standard transformer encoder architecture from NLP
- **Classification Head**: Attaches a simple MLP head for classification tasks

## Performance Achievements

- **ImageNet**: Achieved state-of-the-art results on ImageNet-21k pre-training
- **Efficiency**: Required substantially fewer computational resources than equivalent ResNet models
- **Transfer Learning**: Excellent performance when transferred to various downstream vision tasks
- **Scalability**: Performance continues to improve with larger models and more data

## Significance

Vision Transformers (ViTs) revolutionized computer vision by:

- **Paradigm Shift**: Moved away from the CNN-dominated approach that had dominated vision for decades
- **Unified Architecture**: Showed that the same transformer architecture could excel in both NLP and vision
- **Scalability**: Demonstrated better scaling properties than convolutional architectures
- **Foundation for Modern Vision**: Inspired numerous follow-up works and became the basis for many modern vision models

This work bridged the gap between natural language processing and computer vision, showing that transformers could be universal architectures for multiple domains.